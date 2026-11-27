"""Tests of :mod:`mupif.launcher`: command lines and environments of job processes."""

import os
import sys

from mupif.launcher import Launcher, LocalPythonLauncher


BOOTSTRAP = ['-c', 'import mupif; mupif.ModelServer._spawnedProcessPopen()', '-', b'pickled']


def test_local_python_command_uses_server_interpreter():
    assert LocalPythonLauncher().command(BOOTSTRAP) == [sys.executable, *BOOTSTRAP]


def test_local_python_env_puts_sys_path_before_inherited_pythonpath():
    env = LocalPythonLauncher(pythonPath=['/pkg']).env({'PYTHONPATH': '/inherited', 'X': '1'})
    parts = env['PYTHONPATH'].split(os.pathsep)
    # package directory first, then the server's sys.path, the inherited PYTHONPATH last
    assert parts[0] == '/pkg' and parts[-1] == '/inherited'
    assert parts[1:-1] == list(sys.path)
    assert env['X'] == '1'


def test_local_python_env_without_inherited_pythonpath():
    env = LocalPythonLauncher().env({})
    assert env['PYTHONPATH'] == os.pathsep.join(sys.path)


def test_extra_env_and_path():
    base = {'PATH': '/usr/bin', 'LM_LICENSE_FILE': 'old'}
    env = Launcher(extraEnv={'LM_LICENSE_FILE': '27000@lic'}, extraPath=['/opt/a/bin', '/opt/b/bin']).env(base)
    assert env['PATH'] == os.pathsep.join(['/opt/a/bin', '/opt/b/bin', '/usr/bin'])
    assert env['LM_LICENSE_FILE'] == '27000@lic'
    # the base environment is not changed
    assert base == {'PATH': '/usr/bin', 'LM_LICENSE_FILE': 'old'}


def test_extra_path_without_inherited_path():
    assert Launcher(extraPath=['/opt/a/bin']).env({})['PATH'] == '/opt/a/bin'


# --- PixiLauncher, with the fake pixi of mupif.tests.fakepixi

import subprocess

import pytest

from mupif.launcher import PixiLauncher
from mupif.tests import fakepixi


@pytest.fixture
def pkg(tmp_path):
    d = tmp_path / 'pkg'
    d.mkdir()
    (d / 'pixi.toml').write_text('[project]\nname = "m"\n')
    (d / 'pixi.lock').write_text('version: 6\n')
    return d


def test_pixi_prepare_installs_once_and_activates(tmp_path, pkg):
    pixi = fakepixi.install(tmp_path)
    la = PixiLauncher(pkg, environment='solver', pixi=pixi, extraEnv={'LIC': 'x'}, extraPath=['/opt/tool/bin'])
    with pytest.raises(RuntimeError):  # not prepared yet
        la.command(BOOTSTRAP)
    la.prepare()
    la.prepare()
    assert len((pkg / '.pixi' / 'install-calls').read_text().splitlines()) == 1
    prefix = pkg / '.pixi' / 'envs' / 'solver'
    assert la.command(BOOTSTRAP) == [str(prefix / 'bin' / 'python'), *BOOTSTRAP]
    env = la.env({'PYTHONPATH': '/server/site', 'PYTHONHOME': '/x', 'HOME': '/home/u', 'PATH': '/usr/bin'})
    # the server's Python setup does not leak in; the package is importable; activation applied
    assert env['PYTHONPATH'] == str(pkg) and 'PYTHONHOME' not in env
    assert env['CONDA_PREFIX'] == str(prefix) and env['FAKE_PIXI_ACTIVATED'] == 'solver' and env['HOME'] == '/home/u'
    # host capabilities on top of the activation
    assert env['PATH'].split(os.pathsep)[:2] == ['/opt/tool/bin', str(prefix / 'bin')] and env['LIC'] == 'x'
    # the environment's interpreter really runs
    out = subprocess.run(la.command(['-c', 'import os; print(os.environ["FAKE_PIXI_ACTIVATED"])']), env=la.env(os.environ), capture_output=True, text=True)
    assert out.stdout.strip() == 'solver'


def test_pixi_install_failure_reported(tmp_path, pkg):
    (pkg / 'FAIL').write_text('')
    la = PixiLauncher(pkg, pixi=fakepixi.install(tmp_path))
    with pytest.raises(RuntimeError, match='failed to solve'):
        la.prepare()
    assert la.activation is None


def test_pixi_missing(tmp_path, pkg, monkeypatch):
    monkeypatch.setenv('PIXI_EXE', str(tmp_path / 'nonexistent'))
    monkeypatch.setenv('PATH', str(tmp_path))
    monkeypatch.setenv('HOME', str(tmp_path))
    la = PixiLauncher(pkg)
    assert la.pixi is None
    with pytest.raises(RuntimeError, match='pixi not found'):
        la.prepare()


def test_pixi_found_by_env_variable(tmp_path, monkeypatch):
    pixi = fakepixi.install(tmp_path)
    monkeypatch.setenv('PIXI_EXE', pixi)
    assert PixiLauncher.findPixi() == pixi


def test_model_server_gives_launcher_job_env_and_work_dir(tmp_path):
    'The model server hands the launcher the job MUPIF_* variables (in env()) and the work directory (in command()).'
    from mupif.modelserver import ModelServer
    seen = {}

    class Recording(LocalPythonLauncher):
        def env(self, base):
            seen['env'] = {k: v for k, v in base.items() if k.startswith('MUPIF_LOG_')}
            return super().env(base)

        def command(self, bootstrap, *, workDir=None):
            seen['workDir'] = workDir
            # a job which fails at once: only what the launcher received is checked here
            return [sys.executable, '-c', 'raise SystemExit(3)']

    from mupif.tests import testApp
    # no nameserver needed: the job fails before anything is registered (only its URI string is used)
    fakeNS = type('NS', (), {'_pyroUri': 'PYRO:ns@127.0.0.1:1'})()
    srv = ModelServer(ns=fakeNS, appName='rec', appClass=testApp.testApp, workDir=str(tmp_path), launcher=Recording())
    srv.jobStartTimeout = 2
    srv._discardJob = lambda proc, jobID: None
    with pytest.raises(RuntimeError):
        srv._allocateJob('user', remoteLogUri='PYRO:log@h:1', spec=ModelServer.JobSpec(appClass=testApp.testApp, launcher=srv.launcher))
    assert seen['env'] == {'MUPIF_LOG_PYRO': 'PYRO:log@h:1', 'MUPIF_LOG_LEVEL': 'DEBUG', 'MUPIF_LOG_PROCESSNAME': '1@rec'}
    assert seen['workDir'] == srv.getJobWorkDir('1@rec')


# --- ApptainerLauncher, with the fake apptainer of mupif.tests.fakeapptainer

import hashlib

from mupif.launcher import ApptainerLauncher
from mupif.tests import fakeapptainer

H = 'a' * 64


@pytest.fixture
def fakeApptainer(tmp_path):
    d = tmp_path / 'bin'
    d.mkdir()
    return d, fakeapptainer.install(d)


def test_apptainer_pulls_registry_image_once(tmp_path, pkg, fakeApptainer):
    bindir, exe = fakeApptainer
    la = ApptainerLauncher(pkg, image=f'docker://ghcr.io/x/m@sha256:{H}', apptainer=exe)
    la.prepare()
    la.prepare()
    assert la.sif.read_text() == f'fake image docker://ghcr.io/x/m@sha256:{H}'
    # pulled once, to a temporary file next to the image (renamed into place when complete)
    (pull,) = fakeapptainer.calls(bindir)
    assert pull[:2] == ['pull', '--disable-cache'] and pull[3] == f'docker://ghcr.io/x/m@sha256:{H}'
    assert os.path.dirname(pull[2]) == str(la.sif.parent) and pull[2] != str(la.sif)
    # a new launcher (server restarted) finds the image in the package cache entry
    ApptainerLauncher(pkg, image=f'docker://ghcr.io/x/m@sha256:{H}', apptainer=exe).prepare()
    assert len(fakeapptainer.calls(bindir)) == 1


def test_apptainer_pull_failure(tmp_path, pkg, fakeApptainer):
    la = ApptainerLauncher(pkg, image=f'docker://ghcr.io/x/missing@sha256:{H}', apptainer=fakeApptainer[1])
    with pytest.raises(RuntimeError, match='failed to get image'):
        la.prepare()
    assert not la.sif.exists() and list(la.sif.parent.iterdir()) == []


def test_apptainer_sif_file_verified(tmp_path, pkg, fakeApptainer):
    sif = tmp_path / 'shared' / 'model.sif'
    sif.parent.mkdir()
    sif.write_bytes(b'SIF image content')
    good = 'sha256:' + hashlib.sha256(b'SIF image content').hexdigest()
    la = ApptainerLauncher(pkg, image=f'file://{sif}', imageDigest=good, apptainer=fakeApptainer[1])
    la.prepare()
    assert la.sif.read_bytes() == b'SIF image content'
    # changed on the shared file system since it was published: refused, nothing kept
    other = tmp_path / 'pkg2'
    other.mkdir()
    sif.write_bytes(b'tampered')
    la2 = ApptainerLauncher(other, image=f'file://{sif}', imageDigest=good, apptainer=fakeApptainer[1])
    with pytest.raises(RuntimeError, match='refusing'):
        la2.prepare()
    assert not la2.sif.exists() and list(la2.sif.parent.iterdir()) == []


def test_apptainer_command_and_env(tmp_path, pkg, fakeApptainer):
    exe = fakeApptainer[1]
    la = ApptainerLauncher(pkg, image=f'oras://r/m@sha256:{H}', gpu=True, python='/opt/py/bin/python', binds=['/opt/abaqus'],
                           apptainer=exe, extraEnv={'LM_LICENSE_FILE': '27000@lic'}, extraPath=['/opt/abaqus/bin'])
    cmd = la.command(BOOTSTRAP, workDir='/work/1@x')
    assert cmd == [exe, 'exec', '--contain', '--cleanenv', '--nv', '--bind', '/work/1@x:/work/1@x', '--bind', f'{pkg}:/mupif/package:ro',
                   '--bind', '/opt/abaqus:/opt/abaqus:ro', str(la.sif), '/opt/py/bin/python', *BOOTSTRAP]
    env = la.env({'PATH': '/usr/bin', 'PYTHONPATH': '/server/site', 'MUPIF_LOG_LEVEL': 'DEBUG', 'MUPIF_LOG_PYRO': 'PYRO:l@h:1',
                  'APPTAINERENV_LEAK': 'x', 'HOME': '/home/u'})
    # the apptainer process runs with the server's environment, without variables meant for containers
    assert env['PATH'] == '/usr/bin' and env['HOME'] == '/home/u' and 'APPTAINERENV_LEAK' not in env
    inside = {k[len('APPTAINERENV_'):]: v for k, v in env.items() if k.startswith('APPTAINERENV_')}
    assert inside == {'MUPIF_LOG_LEVEL': 'DEBUG', 'MUPIF_LOG_PYRO': 'PYRO:l@h:1', 'LM_LICENSE_FILE': '27000@lic',
                      'PYTHONPATH': '/mupif/package', 'PREPEND_PATH': '/opt/abaqus/bin'}
    with pytest.raises(ValueError):
        la.command(BOOTSTRAP)  # the work directory must be given
    with pytest.raises(ValueError):
        ApptainerLauncher(pkg, image=f'oras://r/m@sha256:{H}', binds=['/a:b'], apptainer=exe)


def test_apptainer_job_runs(tmp_path, pkg, fakeApptainer):
    'Through the fake: the job sees the package on PYTHONPATH, the variables passed in, not the server ones.'
    la = ApptainerLauncher(pkg, image=f'docker://r/m@sha256:{H}', apptainer=fakeApptainer[1], extraEnv={'LIC': 'x'})
    la.prepare()
    code = 'import os, sys; print(os.environ.get("PYTHONPATH"), os.environ.get("LIC"), os.environ.get("SECRET"), os.environ.get("MUPIF_LOG_LEVEL"))'
    out = subprocess.run(la.command(['-c', code], workDir=str(tmp_path)), env=la.env(dict(os.environ, SECRET='s', MUPIF_LOG_LEVEL='INFO')),
                         capture_output=True, text=True)
    assert out.stdout.split() == [str(pkg), 'x', 'None', 'INFO'], out.stderr
