import sys
sys.path.append('../..')

import unittest
import Pyro4
import Pyro4.naming
import time
import mupif
import mupif.tests.testApp as testApp
import multiprocessing
import subprocess


Pyro4.config.SERIALIZER = "serpent"
Pyro4.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED = {'serpent'}
Pyro4.config.SERVERTYPE = "multiplex"

# start nameserver on localhost, port 9092

class SimpleJobManager_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nsloop=multiprocessing.Process(target=Pyro4.naming.startNSloop,kwargs=dict(host='127.0.0.1',port=9092,hmac=None))
        cls.nsloop.start()
        #cls.nsproc=subprocess.Popen(['pyro4-ns', '-p', '9092', '-n', '127.0.0.1'], 
        #    stdout=sys.stdin, stderr=sys.stderr)
        print ("nameserver started")
        #print (cls.nsproc, cls.nsproc.pid)
        time.sleep(1)
        cls.ns = mupif.PyroUtil.connectNameServer(nshost='127.0.0.1', nsport=9092, hkey=None)

        cls.jobMan = mupif.SimpleJobManager.SimpleJobManager2(daemon=None, ns=cls.ns, appAPIClass=testApp, appName="app", 
            portRange=(9000, 9030), jobManWorkDir=".", serverConfigPath="/home/bp/devel/mupif.git/mupif/tests", 
            serverConfigFile="serverConfig", serverConfigMode=0, 
            jobMan2CmdPath="/home/bp/devel/mupif.git/mupif/tools/JobMan2cmd.py", maxJobs=2, jobMancmdCommPort=10000)
        # test jobManager
        cls.jobMan.getApplicationSignature()

    @classmethod
    def tearDownClass(cls):
        cls.jobMan.terminate()
        cls.nsloop.terminate()
        cls.nsloop.join()

    def tearDown (self):
        self.jobMan.terminateAllJobs()

    def test_getApplicationSignature(self):
        self.assertTrue(self.jobMan.getApplicationSignature() == 'Mupif.JobManager.SimpleJobManager2')
    
    def test_allocateJob(self):
        self.assertListEqual(self.jobMan.getStatus(), [])
        (retCode, jobId, port) = self.jobMan.allocateJob(user="user", natPort=None, ticket=None)
        self.assertTrue(retCode == mupif.JobManager.JOBMAN_OK)
    
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
        with self.assertRaises(mupif.JobManager.JobManNoResourcesException) as cm:
            self.jobMan.allocateJob(user="user", natPort=None, ticket=None)    
        (retCode2, jobId2, port2) = self.jobMan.allocateJob(user="user", natPort=None, ticket=ticket)
        print("Retcode2 "+str(retCode2))

        
        


if __name__ == '__main__': unittest.main()