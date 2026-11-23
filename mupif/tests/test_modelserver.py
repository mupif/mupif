import sys, os.path
#sys.path.append('../..')
thisDir=os.path.dirname(os.path.abspath(__file__))
sys.path+=[thisDir+'/..',thisDir+'../..']


from mupif.tests import testApp

import unittest
import time
import mupif
import mupif as mp
import mupif.tests.testApp as testApp
import multiprocessing
import subprocess
import importlib

import Pyro5

import pytest

Pyro5.config.SERIALIZER = "serpent"
# Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
# Pyro5.config.SERIALIZERS_ACCEPTED = {'serpent'}
Pyro5.config.SERVERTYPE = "multiplex"

import logging
log=logging.getLogger()

@Pyro5.api.expose
class StdOutErrModel(mp.Model):
    def __init__(self,metadata=None):
        super().__init__()
        self.updateMetadata(metadata)
    def solveStep(self,*args,**kw):
        import sys
        sys.stdout.write('THIS-IS-STDOUT\n')
        sys.stdout.flush()
        sys.stderr.write('THIS-IS-STDERR\n')
        sys.stderr.flush()

@Pyro5.api.expose
class TimeoutModel(mp.Model):
    def __init__(self,metadata=None):
        super().__init__()
        self.updateMetadata({'Timeout':1})
    def solveStep(self,*args,**kw):
        import time
        time.sleep(10)

@Pyro5.api.expose
class SlowStartModel(mp.Model):
    'A model whose job takes longer to start than the model server waits for it.'
    def __init__(self,metadata=None):
        super().__init__()
        import time, os
        # quick in the model server's own process (it instantiates the class for its metadata);
        # slow in the job process, which the server tells by the environment of the spawned job
        if os.environ.get('MUPIF_LOG_PROCESSNAME','').endswith('@appSlow'): time.sleep(5)

# find free port so that previously hung test does not block us
def availablePort(p0,p1,host='127.0.0.1'):
    import socket
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    for p in range(p0,p1+1):
        try:
            s.bind((host,p))
            s.close()
            return p
        except: pass
    raise RuntimeError(f'No free port at {host}:{p0}…{p1}')

def waitPort(hostPort,timeout=10,dt=.1):
    import socket,time
    s=socket.socket()
    t0=time.time()
    s.settimeout(dt)
    while True:
        try:
            s.connect(hostPort)
            return
        except OSError:
            if time.time()-t0>timeout: raise RuntimeError(f'Timeout {timeout} s connecting to {hostPort[0]}:{hostPort[1]}')
            time.sleep(dt)

class ModelServer_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        # skip all tests under windows (fails, cause unknown)
        # also fails under Github Workflows (localhost connection refused... why?)
        if sys.platform.startswith('win') or 'GITHUB_ACTION' in os.environ:
            raise unittest.SkipTest('Would fail under Windows and github actions (localhost connection refused, unclear)')


        import tempfile
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name

        nsPort=availablePort(9062,9099)
        # it seems that 0.0.0.0 (INADDR_ANY) does not bind local interfaces on windows (?)
        # use straight localhost instead
        try:
            cls.nsloop=multiprocessing.Process(target=Pyro5.nameserver.start_ns_loop,kwargs=dict(host='127.0.0.1',port=nsPort))
            cls.nsloop.start()
            log.info("nameserver started")
            waitPort(('127.0.0.1',nsPort))
        except:
            cls.nsloop.kill()
            raise
        cls.ns = mupif.pyroutil.connectNameserver(nshost='localhost', nsport=nsPort)

        cls.jobMan = mupif.modelserver.ModelServer(
            ns=cls.ns,
            appName="app",
            workDir=cls.tmp,
            appClass=testApp.testApp,
            maxJobs=2
        )
        # test jobManager
        cls.jobMan.getApplicationSignature()

        cls.daemon=mp.pyroutil.getDaemon(proxy=cls.ns)

    @classmethod
    def tearDownClass(cls):
        cls.jobMan.terminate()
        cls.nsloop.terminate()
        cls.nsloop.join()
        cls.tmpdir.cleanup()


    def tearDown (self):
        self.jobMan.terminateAllJobs()

    def test_getApplicationSignature(self):
        self.assertEqual(self.jobMan.getApplicationSignature(),'Mupif.JobManager.ModelServer')

    def test_getModelMetadata(self):
        self.assertEqual(self.jobMan.getModelMetadata()['ID'],'mupif-tests-testApp')
    
    def test_allocateJob(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", ticket=None)
        self.assertTrue(retCode == mupif.jobmanager.JOBMAN_OK)
    
    def test_getStatus(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", ticket=None)
        retCode2 = self.jobMan.getStatus()
        print(retCode2)
        self.assertTrue(len(retCode2) == 1)
    
    def test_terminateJob(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", ticket=None)
        retCode2 = self.jobMan.getStatus() 
        self.assertTrue(len(retCode2) == 1)
        self.jobMan.terminateJob(jobId)
        retCode2 = self.jobMan.getStatus() 
        self.assertTrue(len(retCode2) == 0)

    def test_terminateAllJobs(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", ticket=None)
        self.assertTrue(len(self.jobMan.getStatus()) == 1)
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user", ticket=None)

        self.assertTrue(len(self.jobMan.getStatus()) == 2)
        self.jobMan.terminateAllJobs()
        self.assertTrue(len(self.jobMan.getStatus()) == 0)

    def test_preallocate(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        ticket = self.jobMan.preAllocate(requirements=None)
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", ticket=None)
        print ("Retcode "+str(retCode))
        with self.assertRaises(mupif.modelserverbase.ModelServerNoResourcesException) as cm:
            self.jobMan.allocateJob(user="user", ticket=None)
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user",ticket=ticket)
        print("Retcode2 "+str(retCode2))

    def test_jobLog(self):
        cls=self.__class__
        jobManOut=mp.ModelServer(ns=cls.ns,appName='appOut',workDir=cls.tmp,appClass=StdOutErrModel,maxJobs=1)
        uri=cls.daemon.register(jobManOut)
        jobManOut.registerPyro(daemon=cls.daemon,ns=cls.ns,uri=uri,appName=jobManOut.appName,exclusiveDaemon=False)
        self.assertEqual(jobManOut.getStatus(),[])
        (retCode,jobId,port)=jobManOut.allocateJob(user='user')
        self.assertEqual(retCode,mp.jobmanager.JOBMAN_OK)
        stat=jobManOut.getStatus()
        self.assertEqual(len(stat),1)
        state=jobManOut.getStatusExtended()
        self.assertEqual(len(state.currJobs),1)
        self.assertEqual(state.totalJobs,1)
        jobId=stat[0].key
        uri=stat[0].uri
        mod=Pyro5.api.Proxy(uri)
        mod.solveStep()
        mod.terminate()
        jobManOut.terminateJob(jobId)
        stat=jobManOut.getStatus() # this will update job statuses internally
        log=jobManOut.getLogFile(jobId)
        log2=f'{cls.tmp}/job.log'
        mp.PyroFile.copy(log,log2)
        dta=open(log2,'r').read()
        self.assertTrue('THIS-IS-STDOUT' in dta)
        self.assertTrue('THIS-IS-STDERR' in dta)

    def test_timeout(self):
        cls=self.__class__
        jobManTime=mp.ModelServer(ns=cls.ns,appName='appTimeout',workDir=cls.tmp,appClass=TimeoutModel,maxJobs=1)
        uri=cls.daemon.register(jobManTime)
        jobManTime.registerPyro(daemon=cls.daemon,ns=cls.ns,uri=uri,appName=jobManTime.appName,exclusiveDaemon=False)
        self.assertEqual(jobManTime.getStatus(),[])
        (retCode,jobId,port)=jobManTime.allocateJob(user='user')
        self.assertEqual(retCode,mp.jobmanager.JOBMAN_OK)
        time.sleep(2) # this will trigger the timeout of 1s
        stat=jobManTime.getStatus()
        self.assertEqual(len(stat),0) # not in active jobs anymore

    def test_preallocateTicketExpires(self):
        'An unused ticket stops holding its slot after ticketExpireTimeout (it used to hold it forever).'
        self.assertEqual(self.jobMan.getNumberOfFreeJobs(),2)
        ticket=self.jobMan.preAllocate()
        self.assertIsInstance(ticket,str)
        self.assertEqual(self.jobMan.getNumberOfFreeJobs(),1)
        old=mp.ModelServer.ticketExpireTimeout
        mp.ModelServer.ticketExpireTimeout=0.2
        try:
            time.sleep(0.3)
            self.assertEqual(self.jobMan.getNumberOfFreeJobs(),2)
            # an expired ticket gives no privilege: with both slots taken, it is refused
            self.jobMan.allocateJob(user='user')
            self.jobMan.allocateJob(user='user')
            with self.assertRaises(mupif.modelserverbase.ModelServerNoResourcesException):
                self.jobMan.allocateJob(user='user',ticket=ticket)
        finally:
            mp.ModelServer.ticketExpireTimeout=old

    def test_preallocateOverPyro(self):
        'A ticket obtained and used over Pyro (where it travels as a string) is recognised and used up.'
        cls=self.__class__
        srv=mp.ModelServer(ns=cls.ns,appName='appTicket',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
        uri=cls.daemon.register(srv)
        srv.registerPyro(daemon=cls.daemon,ns=cls.ns,uri=uri,appName='appTicket',exclusiveDaemon=False)
        try:
            remote=Pyro5.api.Proxy(uri)
            ticket=remote.preAllocate()
            self.assertEqual(remote.getNumberOfFreeJobs(),0)
            (retCode,jobId,port)=remote.allocateJob('user',ticket=ticket)
            self.assertEqual(retCode,mp.jobmanager.JOBMAN_OK)
            # the ticket is used up: the slot is taken by the job, not by the job and the ticket
            self.assertEqual(srv.tickets,{})
            remote.terminateJob(jobId)
            self.assertEqual(remote.getNumberOfFreeJobs(),1)
        finally:
            srv.terminate(force=True)

    def test_failedAllocationLeavesNoJob(self):
        'A job which does not start in time is killed (it used to run on unknown to the server, an orphan).'
        import psutil
        cls=self.__class__
        srv=mp.ModelServer(ns=cls.ns,appName='appSlow',workDir=cls.tmp,appClass=SlowStartModel,maxJobs=1)
        srv.jobStartTimeout=1
        uri=cls.daemon.register(srv)
        srv.registerPyro(daemon=cls.daemon,ns=cls.ns,uri=uri,appName='appSlow',exclusiveDaemon=False)
        def jobs(): return [p for p in psutil.process_iter(['cmdline']) if any('1@appSlow' in c for c in (p.info['cmdline'] or []))]
        try:
            with self.assertRaises(RuntimeError): srv.allocateJob(user='user')
            self.assertEqual(jobs(),[])
            with self.assertRaises(Pyro5.errors.NamingError): cls.ns.lookup('1@appSlow')
            # the slot is free again
            self.assertEqual(srv.getNumberOfFreeJobs(),1)
        finally:
            for p in jobs(): p.kill()
            srv.terminate(force=True)

    def test_jobIdUsesRegisteredName(self):
        'Jobs of a server registered under an instance name are named after that name, so that jobs of two instances do not collide.'
        cls=self.__class__
        inst=mp.ModelServer(ns=cls.ns,appName='appInst',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
        self.assertEqual(inst.getNSName(),'appInst') # not registered yet: the base name
        uri=cls.daemon.register(inst)
        inst.registerPyro(daemon=cls.daemon,ns=cls.ns,uri=uri,appName='appInst#2',exclusiveDaemon=False)
        cls.ns.register('appInst#2',uri)
        self.assertEqual(inst.getName(),'appInst')
        self.assertEqual(inst.getNSName(),'appInst#2')
        try:
            (retCode,jobId,port)=inst.allocateJob(user='user')
            self.assertEqual(jobId,'1@appInst#2')
        finally:
            inst.terminate(force=True)
        # terminate removed its own registration
        with self.assertRaises(Pyro5.errors.NamingError): cls.ns.lookup('appInst#2')

    def test_modelServerNSName(self):
        'Registered name: base name if free or stale, an instance name if a live server holds it or an instance id is given.'
        cls=self.__class__
        nsName=mp.pyroutil.modelServerNSName
        srv=mp.ModelServer(ns=cls.ns,appName='appNaming',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
        # free name
        self.assertEqual(nsName(cls.ns,srv),'appNaming')
        # stale entry (nothing answers there): taken over
        cls.ns.register('appNaming','PYRO:gone@127.0.0.1:1')
        self.assertEqual(nsName(cls.ns,srv,aliveTimeout=1),'appNaming')
        # a live server holds the base name: this one gets an instance name
        live=mp.ModelServer(ns=cls.ns,appName='appNaming',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
        uri=cls.daemon.register(live)
        cls.ns.register('appNaming',uri)
        try:
            import socket
            self.assertEqual(nsName(cls.ns,srv),f'appNaming~{socket.gethostname()}-{os.getpid()}')
        finally:
            cls.ns.remove('appNaming')
            cls.daemon.unregister(live)
        # explicit instance id, from the argument or from the environment
        self.assertEqual(nsName(cls.ns,mp.ModelServer(ns=cls.ns,appName='appNaming',workDir=cls.tmp,appClass=testApp.testApp,instance='node2')),'appNaming~node2')
        os.environ['MUPIF_MODELSERVER_INSTANCE']='node3'
        try:
            self.assertEqual(nsName(cls.ns,mp.ModelServer(ns=cls.ns,appName='appNaming',workDir=cls.tmp,appClass=testApp.testApp)),'appNaming~node3')
        finally:
            del os.environ['MUPIF_MODELSERVER_INSTANCE']
        with self.assertRaises(ValueError):
            mp.ModelServer(ns=cls.ns,appName='appNaming',workDir=cls.tmp,appClass=testApp.testApp,instance='node 2')

    def test_workflowPlacesModelsOnInstances(self):
        'A workflow allocates its model on the least loaded instance of the model server, and reports where.'
        cls=self.__class__
        # the servers get a daemon of their own, serving requests in threads: allocateJob blocks
        # until the spawned job is up, and the job logs to the workflow's log receiver, which is in
        # the (single-threaded) class daemon; sharing it would deadlock (as it never happens when
        # model servers run in their own processes)
        import threading
        serverType,Pyro5.config.SERVERTYPE=Pyro5.config.SERVERTYPE,'thread'
        try: daemon=Pyro5.api.Daemon(host='127.0.0.1')
        finally: Pyro5.config.SERVERTYPE=serverType
        threading.Thread(target=daemon.requestLoop,daemon=True).start()
        servers={}
        for nsName in ('appWf','appWf~2'):
            srv=mp.ModelServer(ns=cls.ns,appName='appWf',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=2)
            uri=daemon.register(srv)
            srv.registerPyro(daemon=daemon,ns=cls.ns,uri=uri,appName=nsName,exclusiveDaemon=False)
            # the tags runModelServer would give (testApp has no Solver metadata for modelServerTags)
            cls.ns.register(nsName,uri,metadata={'type:jobmanager','appWf','mupif:tickets-v2'})
            servers[nsName]=srv

        class Wf(mp.Workflow):
            def __init__(self,metadata=None):
                super().__init__(metadata={'Name':'wf','ID':'wf','Description':'','Inputs':[],'Outputs':[],'Models':[{'Name':'m','Jobmanager':'appWf'}]})
            # testApp has too little metadata (no Solver) for the dependency record; not tested here
            def generateModelDependencies(self): pass

        nsPrev=os.environ.get('MUPIF_NS')
        os.environ['MUPIF_NS']=f'{cls.ns._pyroUri.host}:{cls.ns._pyroUri.port}'
        workflows=[]
        def start():
            wf=Wf()
            workflows.append(wf)
            wf.initialize(metadata={'Execution':{'ID':'1','Use_case_ID':'1','Task_ID':'1'}})
            return wf.getModelServers()['m']
        try:
            # one slot of the base-name instance is taken: the other instance is less loaded
            servers['appWf'].allocateJob(user='other')
            self.assertEqual(start(),'appWf~2')
            # both at 50 %: either; then the remaining one
            first=start()
            self.assertIn(first,servers)
            self.assertEqual(start(),'appWf~2' if first=='appWf' else 'appWf')
            # all four slots taken: no resources (the scheduler would retry later)
            with self.assertRaises(mp.modelserverbase.ModelServerNoResourcesException):
                start()
        finally:
            if nsPrev is None: del os.environ['MUPIF_NS']
            else: os.environ['MUPIF_NS']=nsPrev
            for wf in workflows:
                try: wf.terminate()
                except Exception: pass
            for srv in servers.values():
                srv.terminate(force=True)
            daemon.shutdown()

    def test_removeStaleModelServers(self):
        'Entries of crashed instances (not answering) of the base name are removed; live ones and other models stay.'
        cls=self.__class__
        live=mp.ModelServer(ns=cls.ns,appName='appStale',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
        uri=cls.daemon.register(live)
        cls.ns.register('appStale',uri,metadata={'type:jobmanager','appStale'})
        cls.ns.register('appStale~gone',f'PYRO:gone@127.0.0.1:1',metadata={'type:jobmanager','appStale'})
        cls.ns.register('other~gone',f'PYRO:gone@127.0.0.1:1',metadata={'type:jobmanager','other'})
        try:
            self.assertEqual(mp.pyroutil.removeStaleModelServers(cls.ns,'appStale',aliveTimeout=1),['appStale~gone'])
            self.assertEqual(str(cls.ns.lookup('appStale')),str(uri))
            with self.assertRaises(Pyro5.errors.NamingError): cls.ns.lookup('appStale~gone')
            cls.ns.lookup('other~gone')
        finally:
            for n in ('appStale','other~gone'): cls.ns.remove(n)
            cls.daemon.unregister(live)

    def test_watchRegistration(self):
        'A server registers again when its entry disappears or points to a dead server, but not over a live one, and not after it stopped.'
        import threading
        cls=self.__class__
        own='PYRO:own@127.0.0.1:2'
        def waitFor(cond,timeout=5):
            t0=time.time()
            while not cond():
                if time.time()-t0>timeout: return False
                time.sleep(0.05)
            return True
        def current():
            try: return str(cls.ns.lookup('appWatch'))
            except Pyro5.errors.NamingError: return None
        cls.ns.register('appWatch',own,metadata={'type:jobmanager','appWatch'})
        stop=threading.Event()
        t=threading.Thread(target=mp.pyroutil.watchRegistration,args=(cls.ns._pyroUri,'appWatch',own,{'type:jobmanager','appWatch'},stop,0.1),daemon=True)
        t.start()
        try:
            # removed (nameserver restart, or a client gave up on the server): registered again, with its tags
            cls.ns.remove('appWatch')
            self.assertTrue(waitFor(lambda: current()==own))
            self.assertEqual(set(cls.ns.lookup('appWatch',return_metadata=True)[1]),{'type:jobmanager','appWatch'})
            # taken over by a server which does not answer: taken back
            cls.ns.register('appWatch','PYRO:gone@127.0.0.1:1')
            self.assertTrue(waitFor(lambda: current()==own))
            # taken over by a live server: left alone
            other=mp.ModelServer(ns=cls.ns,appName='appWatch',workDir=cls.tmp,appClass=testApp.testApp,maxJobs=1)
            otherUri=str(cls.daemon.register(other))
            cls.ns.register('appWatch',otherUri)
            time.sleep(0.5)
            self.assertEqual(current(),otherUri)
            cls.daemon.unregister(other)
            # stopped (the server left the nameserver itself): not registered again
            stop.set()
            t.join(2)
            cls.ns.remove('appWatch')
            time.sleep(0.3)
            self.assertIsNone(current())
        finally:
            stop.set()
            if current() is not None: cls.ns.remove('appWatch')

    def test_removeOwnRegistration(self):
        'A server leaving the nameserver does not remove an entry another server registered under the same name meanwhile.'
        cls=self.__class__
        ours,theirs='PYRO:ours@127.0.0.1:1','PYRO:theirs@127.0.0.1:2'
        cls.ns.register('shared-name',theirs)
        self.assertFalse(mp.pyroutil.removeOwnRegistration(cls.ns,'shared-name',ours))
        self.assertEqual(str(cls.ns.lookup('shared-name')),theirs)
        self.assertTrue(mp.pyroutil.removeOwnRegistration(cls.ns,'shared-name',theirs))
        with self.assertRaises(Pyro5.errors.NamingError): cls.ns.lookup('shared-name')
        # nothing registered: nothing to remove
        self.assertFalse(mp.pyroutil.removeOwnRegistration(cls.ns,'shared-name',theirs))
        # unknown URI: removed unconditionally (the behaviour before the check was added)
        cls.ns.register('shared-name',theirs)
        self.assertTrue(mp.pyroutil.removeOwnRegistration(cls.ns,'shared-name',None))




if __name__ == '__main__': unittest.main()
