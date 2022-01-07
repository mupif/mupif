import sys, os.path
#sys.path.append('../..')
thisDir=os.path.dirname(os.path.abspath(__file__))
sys.path+=[thisDir+'/..',thisDir+'../..']


import mupif.tests.serverConfig as sc
serverConfig=sc.ServerConfig(mode='localhost')


import unittest
import time
import os
import mupif
import mupif.tests.testApp as testApp
import multiprocessing
import subprocess
import importlib

import Pyro5

Pyro5.config.SERIALIZER = "serpent"
# Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
# Pyro5.config.SERIALIZERS_ACCEPTED = {'serpent'}
Pyro5.config.SERVERTYPE = "multiplex"

import mupif.util
log=mupif.util.setupLogger(None)

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

def waitPort(hostPort,timeout=10,dt=.5):
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
            cls.nsloop=multiprocessing.Process(target=Pyro5.nameserver.start_ns_loop,kwargs=dict(host='localhost',port=nsPort))
            cls.nsloop.start()
            log.info("nameserver started")
            waitPort(('localhost',nsPort))
        except:
            cls.nsloop.kill()
            raise
        cls.ns = mupif.pyroutil.connectNameserver(nshost='localhost', nsport=nsPort)
        serverConfig.nsport=nsPort

        cls.jobMan = mupif.simplejobmanager.SimpleJobManager(
            ns=cls.ns,
            appName="app", 
            workDir=cls.tmp,
            appClass=serverConfig.applicationClass,
            maxJobs=2
        )
        # test jobManager
        cls.jobMan.getApplicationSignature()

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
    
    def test_allocateJob(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        self.assertTrue(retCode == mupif.jobmanager.JOBMAN_OK)
    
    def test_getStatus(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        retCode2 = self.jobMan.getStatus() 
        print(retCode2)
        self.assertTrue(len(retCode2) == 1)
    
    def test_terminateJob(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        retCode2 = self.jobMan.getStatus() 
        self.assertTrue(len(retCode2) == 1)
        self.jobMan.terminateJob(jobId)
        retCode2 = self.jobMan.getStatus() 
        self.assertTrue(len(retCode2) == 0)

    def test_terminateAllJobs(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        self.assertTrue(len(self.jobMan.getStatus()) == 1)
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)

        self.assertTrue(len(self.jobMan.getStatus()) == 2)
        self.jobMan.terminateAllJobs()
        self.assertTrue(len(self.jobMan.getStatus()) == 0)

    def test_preallocate(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        ticket = self.jobMan.preAllocate(requirements=None)
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        print ("Retcode "+str(retCode))
        with self.assertRaises(mupif.jobmanager.JobManNoResourcesException) as cm:
            self.jobMan.allocateJob(user="user", natPort=None, ticket=None)    
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user", natPort=None, ticket=ticket)
        print("Retcode2 "+str(retCode2))



        

if __name__ == '__main__': unittest.main()
