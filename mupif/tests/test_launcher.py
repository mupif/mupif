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
