"""
Tests of :class:`mupif.ExecutionServer`: model packages of a registry run on demand.

A nameserver runs for the whole module. Packages are in a :class:`mupif.modelpackage.DirectoryRegistry`;
their model subclasses ``mupif.tests.testApp.testApp`` and reports where and how it runs. The pixi
runtime uses the fake pixi of :mod:`mupif.tests.fakepixi` (no network).
"""

import multiprocessing
import os
import sys
import time

import pytest
import Pyro5
import Pyro5.api
import Pyro5.nameserver

import mupif as mp
from mupif import modelpackage as mpk
from mupif.tests import fakepixi
from mupif.tests.test_modelserver import availablePort, waitPort

pytestmark = pytest.mark.skipif(sys.platform.startswith('win') or 'GITHUB_ACTION' in os.environ,
                                reason='as test_modelserver: localhost connections fail there')

MODEL = '''
import os, sys
import Pyro5.api
from mupif.tests.testApp import testApp

@Pyro5.api.expose
class PkgModel(testApp):
    def where(self):
        return {'file': __file__, 'pythonpath': os.environ.get('PYTHONPATH', ''),
                'activated': os.environ.get('FAKE_PIXI_ACTIVATED'), 'lic': os.environ.get('LIC'),
                'path': os.environ.get('PATH', '')}
'''


def makePackage(directory, id, runtime='python', requires='[]', version='1.0', fail=False):
    os.makedirs(directory / 'pkgmodel', exist_ok=True)
    (directory / mpk.MANIFEST_NAME).write_text(f'''
ID = "{id}"
Version = "{version}"
Entrypoint = "pkgmodel.model:PkgModel"
RequiresHost = {requires}
[Runtime]
Type = "{runtime}"
''')
    (directory / 'pkgmodel' / '__init__.py').write_text('')
    (directory / 'pkgmodel' / 'model.py').write_text(MODEL)
    if runtime == 'pixi':
        (directory / 'pixi.toml').write_text('[project]\nname = "m"\n')
        (directory / 'pixi.lock').write_text('version: 6\n')
    if fail:
        (directory / 'FAIL').write_text('')  # the fake pixi fails to install it


@pytest.fixture(scope='module')
def env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp('execsrv')
    nsPort = availablePort(9100, 9199)
    nsloop = multiprocessing.Process(target=Pyro5.nameserver.start_ns_loop, kwargs=dict(host='127.0.0.1', port=nsPort))
    nsloop.start()
    try:
        waitPort(('127.0.0.1', nsPort))
        ns = mp.pyroutil.connectNameserver(nshost='127.0.0.1', nsport=nsPort)
        reg = tmp / 'registry'
        makePackage(reg / 'py', 'pkg-python')
        makePackage(reg / 'pixi', 'pkg-pixi', runtime='pixi')
        makePackage(reg / 'lic', 'pkg-lic', requires='["solverX"]')
        makePackage(reg / 'abq', 'pkg-abaqus', requires='["abaqus"]')
        makePackage(reg / 'broken', 'pkg-broken', runtime='pixi', fail=True)
        daemon = mp.pyroutil.getDaemon(proxy=ns)
        yield dict(tmp=tmp, ns=ns, registry=mpk.DirectoryRegistry(reg), pixi=fakepixi.install(tmp), daemon=daemon)
    finally:
        nsloop.terminate()
        nsloop.join()


@pytest.fixture
def server(env, request):
    """An execution server with 2 slots, python and pixi runtimes, host capability solverX."""
    name = 'exec-' + request.node.name.replace('_', '-')
    srv = mp.ExecutionServer(ns=env['ns'], appName=name, registry=env['registry'], cacheDir=env['tmp'] / ('cache-' + name),
                             workDir=str(env['tmp']), maxJobs=2, allowPythonRuntime=True, pixi=env['pixi'],
                             hostCapabilities={'solverX': {'Version': '3', 'Env': {'LIC': '27000@lic'}, 'Path': ['/opt/solverX/bin']}})
    uri = env['daemon'].register(srv)
    srv.registerPyro(daemon=env['daemon'], ns=env['ns'], uri=uri, appName=name, exclusiveDaemon=False)
    yield srv
    srv.terminate(force=True)


def run(srv, modelID, **kw):
    """Allocate a job of *modelID*; return (jobID, proxy of the model)."""
    retCode, jobID, port = srv.allocateJob(user='user', modelID=modelID, **kw)
    assert retCode == mp.modelserverbase.JOBMAN_OK
    uri = next(s.uri for s in srv.getStatus() if s.key == jobID)
    return jobID, Pyro5.api.Proxy(uri)


def test_python_package_runs_from_cache(env, server):
    jobID, model = run(server, 'pkg-python')
    where = model.where()
    ref = env['registry'].resolve('pkg-python')
    pkgDir = server.cache.packageDir(ref)
    # the model code is the cached copy of the package, importable through PYTHONPATH
    assert where['file'] == str(pkgDir / 'pkgmodel' / 'model.py')
    assert where['pythonpath'].split(os.pathsep)[0] == str(pkgDir)
    assert model.getMetadata('ID') == 'mupif-tests-testApp'
    assert server.getJobPackage(jobID) == {'ID': 'pkg-python', 'Version': '1.0', 'Digest': ref.digest}
    server.terminateJob(jobID)
    assert server.getStatus() == []
    # still known after the job ended (recorded by workflows after allocation)
    assert server.getJobPackage(jobID)['ID'] == 'pkg-python'
    assert server.getJobPackage('nope') is None


def test_pixi_package_runs_in_its_environment(env, server):
    jobID, model = run(server, 'pkg-pixi')
    where = model.where()
    pkgDir = server.cache.packageDir(env['registry'].resolve('pkg-pixi'))
    assert where['activated'] == 'default'
    # only the package directory: the server's sys.path does not leak into the environment
    assert where['pythonpath'] == str(pkgDir)
    # a second job: the environment is not installed again
    jobID2, _ = run(server, 'pkg-pixi')
    assert len((pkgDir / '.pixi' / 'install-calls').read_text().splitlines()) == 1
    server.terminateJob(jobID)
    server.terminateJob(jobID2)


def test_host_capability_given_to_models_requiring_it(env, server):
    jobID, model = run(server, 'pkg-lic')
    where = model.where()
    assert where['lic'] == '27000@lic' and where['path'].split(os.pathsep)[0] == '/opt/solverX/bin'
    server.terminateJob(jobID)
    # a model not requiring it does not get it
    jobID, model = run(server, 'pkg-python')
    assert model.where()['lic'] is None
    server.terminateJob(jobID)


@pytest.mark.parametrize('modelID,match', [
    ('no-such-model', 'No model package'),
    ('pkg-abaqus', 'host capabilities'),
    ('pkg-broken', 'failed to solve'),
    (None, 'model ID must be given'),
])
def test_refusals(server, modelID, match):
    with pytest.raises(mp.ModelServerCannotRunException, match=match):
        server.allocateJob(user='user', modelID=modelID)
    assert server.getStatus() == [] and server.getNumberOfFreeJobs() == 2


def test_broken_package_refused_fast_the_second_time(server):
    with pytest.raises(mp.ModelServerCannotRunException):
        server.allocateJob(user='user', modelID='pkg-broken')
    with pytest.raises(mp.ModelServerCannotRunException, match='failed recently'):
        server.allocateJob(user='user', modelID='pkg-broken')


def test_runtime_not_supported(env):
    srv = mp.ExecutionServer(ns=env['ns'], appName='exec-pixi-only', registry=env['registry'], cacheDir=env['tmp'] / 'cache-pixi-only',
                             workDir=str(env['tmp']), pixi=env['pixi'])
    assert srv.runtimes == {'pixi'}
    with pytest.raises(mp.ModelServerCannotRunException, match="runtime 'python'"):
        srv.allocateJob(user='user', modelID='pkg-python')
    with pytest.raises(ValueError):
        mp.ExecutionServer(ns=env['ns'], appName='x', registry=env['registry'], cacheDir=env['tmp'] / 'c', runtimes=['pixi'], pixi=str(env['tmp'] / 'none'))


def test_full_server_refuses_before_getting_package(env, server):
    jobs = [run(server, 'pkg-python')[0] for _ in range(2)]
    with pytest.raises(mp.ModelServerNoResourcesException):
        server.allocateJob(user='user', modelID='pkg-pixi')
    # the package was not even downloaded
    assert not server.cache.isReady(env['registry'].resolve('pkg-pixi'))
    for j in jobs:
        server.terminateJob(j)


def test_over_pyro_and_tags(env, server):
    remote = Pyro5.api.Proxy(server.pyroURI)
    retCode, jobID, port = remote.allocateJob('user', modelID='pkg-python')
    assert remote.getJobPackage(jobID)['ID'] == 'pkg-python'
    assert remote.getCapabilities() == {'runtimes': ['pixi', 'python'], 'hostCapabilities': {'solverX': '3'}}
    # refusals arrive as an error naming the exception (Pyro may not rebuild the class)
    with pytest.raises(Exception) as ei:
        remote.allocateJob('user', modelID='pkg-abaqus')
    assert 'ModelServerCannotRunException' in (type(ei.value).__name__ + str(ei.value) + ''.join(getattr(ei.value, '_pyroTraceback', [])))
    remote.terminateJob(jobID)
    tags = mp.pyroutil.executionServerTags(server)
    assert {'type:executionserver', server.getName(), 'runtime:pixi', 'runtime:python', 'host:solverX', 'mupif:tickets-v2'} <= tags
    assert 'type:jobmanager' not in tags


REGISTRATION_SCRIPT = r'''
import sys, json
import Pyro5.api
import mupif as mp
from mupif import modelpackage as mpk
nshost, nsport, reg, cache, work, pixi = sys.argv[1:]
ns = mp.pyroutil.connectNameserver(nshost=nshost, nsport=int(nsport))
srv = mp.ExecutionServer(ns=ns, appName='exec-reg', registry=mpk.DirectoryRegistry(reg), cacheDir=cache, workDir=work, pixi=pixi, hostCapabilities={'abaqus': {}})
mp.pyroutil.runExecutionServer(ns=ns, server=srv)
found = ns.yplookup(meta_all={'type:executionserver', 'exec-reg'}, return_metadata=True)
res = {'names': list(found), 'tags': sorted(found['exec-reg'][1]), 'jobmanagers': list(ns.yplookup(meta_all={'type:jobmanager'})),
       'signature': Pyro5.api.Proxy(found['exec-reg'][0]).getApplicationSignature()}
srv.terminate(force=True)
res['afterTerminate'] = 'exec-reg' in ns.list()
print(json.dumps(res))
'''


def test_registration(env):
    """
    runExecutionServer registers the server with its tags; clients looking for model servers
    (type:jobmanager) do not see it; terminate removes it.

    Run in a child process: runServer gives the server an exclusive daemon, which replaces the
    daemon cached by pyroutil.getDaemon for the host and is shut down by terminate, breaking other
    tests of this process which use the cached daemon.
    """
    import json
    import subprocess
    uri = env['ns']._pyroUri
    out = subprocess.run([sys.executable, '-c', REGISTRATION_SCRIPT, uri.host, str(uri.port), str(env['registry'].root),
                          str(env['tmp'] / 'cache-reg'), str(env['tmp']), env['pixi']], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    res = json.loads(out.stdout.strip().splitlines()[-1])
    assert res['names'] == ['exec-reg']
    assert {'type:executionserver', 'runtime:pixi', 'host:abaqus', 'mupif:tickets-v2'} <= set(res['tags'])
    assert 'exec-reg' not in res['jobmanagers']
    assert res['signature'] == 'Mupif.ExecutionServer'
    assert res['afterTerminate'] is False


def test_ready_models_advertised(env, server):
    'A model ready on the server (after its first job) is advertised by ModelID tags, updated in the nameserver.'
    ns = env['ns']
    name = server.getNSName()
    ns.register(name, server.pyroURI, metadata=mp.pyroutil.executionServerTags(server))
    try:
        assert server.readyModels() == []
        assert not any(t.startswith('ModelID:') for t in ns.lookup(name, return_metadata=True)[1])
        jobID, _ = run(server, 'pkg-python')
        server.terminateJob(jobID)
        assert server.readyModels() == ['pkg-python@1.0']
        tags = set(ns.lookup(name, return_metadata=True)[1])
        assert {'ModelID:pkg-python', 'ModelID:pkg-python@1.0', 'type:executionserver'} <= tags
        # clients find it by the model ID among execution servers
        assert name in ns.yplookup(meta_all={'type:executionserver', 'ModelID:pkg-python'})
    finally:
        ns.remove(name)


def test_ready_packages_of_earlier_runs_and_prefetch(env, server):
    'A new server on the same cache knows the packages prepared before; the prefetch list prepares packages ahead of requests.'
    jobID, _ = run(server, 'pkg-python')
    server.terminateJob(jobID)
    again = mp.ExecutionServer(ns=env['ns'], appName='exec-again', registry=env['registry'], cacheDir=server.cache.directory,
                               workDir=str(env['tmp']), allowPythonRuntime=True, pixi=env['pixi'],
                               prefetch=['pkg-pixi@1.0', 'pkg-abaqus', 'no-such-model'])
    assert again.readyModels() == ['pkg-python@1.0']
    th = again.startPrefetch()
    th.join(60)
    # pkg-abaqus is not runnable here and no-such-model does not exist: logged, skipped
    assert again.readyModels() == ['pkg-pixi@1.0', 'pkg-python@1.0']


def test_pruned_package_no_longer_advertised(env, server):
    server.cache.maxBytes = 0  # every package not in use is pruned after each allocation
    j1, _ = run(server, 'pkg-python')
    server.terminateJob(j1)
    j2, _ = run(server, 'pkg-pixi')  # pkg-python is pruned (not in use), pkg-pixi kept (in use)
    try:
        assert server.readyModels() == ['pkg-pixi@1.0']
    finally:
        server.terminateJob(j2)
