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

class SimpleJobManager_TestCase(unittest.TestCase):
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

        cls.jobMan = mupif.simplejobmanager.SimpleJobManager(
            ns=cls.ns,
            appName="app",
            workDir=cls.tmp,
            appClass=testApp.testApp,
            maxJobs=2
        )
        # test jobManager
        cls.jobMan.getApplicationSignature()

        cls.daemon=Pyro5.api.Daemon(host='127.0.0.1')

    @classmethod
    def tearDownClass(cls):
        cls.jobMan.terminate()
        cls.nsloop.terminate()
        cls.nsloop.join()
        cls.tmpdir.cleanup()


    def tearDown (self):
        self.jobMan.terminateAllJobs()

    def test_getApplicationSignature(self):
        self.assertTrue(self.jobMan.getApplicationSignature() == 'Mupif.JobManager.SimpleJobManager')

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
        with self.assertRaises(mupif.jobmanager.JobManNoResourcesException) as cm:
            self.jobMan.allocateJob(user="user", ticket=None)
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user",ticket=ticket)
        print("Retcode2 "+str(retCode2))

    def test_jobLog(self):
        cls=self.__class__
        jobManOut=mp.SimpleJobManager(ns=cls.ns,appName='appOut',workDir=cls.tmp,appClass=StdOutErrModel,maxJobs=1)
        daemon=Pyro5.api.Daemon()
        uri=daemon.register(jobManOut)
        jobManOut.registerPyro(daemon=daemon,ns=cls.ns,uri=uri,appName=jobManOut.appName,externalDaemon=True)
        self.assertEqual(jobManOut.getStatus(),[])
        (retCode,jobId,port)=jobManOut.allocateJob(user='user')
        self.assertEqual(retCode,mp.jobmanager.JOBMAN_OK)
        stat=jobManOut.getStatus()
        self.assertEqual(len(stat),1)
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
        jobManTime=mp.SimpleJobManager(ns=cls.ns,appName='appTimeout',workDir=cls.tmp,appClass=TimeoutModel,maxJobs=1)
        daemon=Pyro5.api.Daemon()
        uri=daemon.register(jobManTime)
        jobManTime.registerPyro(daemon=daemon,ns=cls.ns,uri=uri,appName=jobManTime.appName,externalDaemon=True)
        self.assertEqual(jobManTime.getStatus(),[])
        (retCode,jobId,port)=jobManTime.allocateJob(user='user')
        self.assertEqual(retCode,mp.jobmanager.JOBMAN_OK)
        time.sleep(2) # this will trigger the timeout of 1s
        stat=jobManTime.getStatus()
        self.assertEqual(len(stat),0) # not in active jobs anymore




if __name__ == '__main__': unittest.main()
