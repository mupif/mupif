import sys
sys.path.append('../..')

import unittest
import time
import mupif
import mupif.tests.testApp as testApp
import multiprocessing
import subprocess

import Pyro5

Pyro5.config.SERIALIZER = "serpent"
# Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
# Pyro5.config.SERIALIZERS_ACCEPTED = {'serpent'}
Pyro5.config.SERVERTYPE = "multiplex"

import mupif.util
log=mupif.util.setupLogger(None)

# start nameserver on localhost, port 9092

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
            if time.time()-t0>timeout: raise RuntimeError(f'Timeout {timeout} s connecting to {hostPort[0]}:{hsotPort[1]}')
            time.sleep(dt)

class SimpleJobManager_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name

        nsPort=availablePort(9062,9099)
        cls.nsloop=multiprocessing.Process(target=Pyro5.nameserver.start_ns_loop,kwargs=dict(host='127.0.0.1',port=nsPort))
        cls.nsloop.start()
        log.info("nameserver started")
        waitPort(('127.0.0.1',nsPort))
        #print (cls.nsproc, cls.nsproc.pid)
        cls.ns = mupif.pyroutil.connectNameServer(nshost='127.0.0.1', nsport=nsPort)
        # print('here')
        cls.jobMan = mupif.simplejobmanager.SimpleJobManager2(
            daemon=None,
            ns=cls.ns,
            appAPIClass=testApp,
            appName="app", 
            portRange=(9000, 9030),
            jobManWorkDir=cls.tmp,
            serverConfigPath=mupif.__path__[0]+"/tests", 
            serverConfigFile="serverConfig",
            serverConfigMode=0, 
            jobMan2CmdPath=mupif.__path__[0]+"/tools/JobMan2cmd.py",
            maxJobs=2,
            jobMancmdCommPort=availablePort(10000,10100),
            overrideNsPort=nsPort
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
        self.assertTrue(self.jobMan.getApplicationSignature() == 'Mupif.JobManager.SimpleJobManager2')
    
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
