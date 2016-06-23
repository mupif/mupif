from __future__ import print_function
import unittest
import sys, multiprocessing, time
import unittest,sys
sys.path.append('../..')

import mupif, mupif.Application
import Pyro4

from mupif import PyroUtil

class AnyApp(mupif.Application.Application):
    def __init__(self,f): super(AnyApp,self).__init__(f)
    def getApplicationSignature(self): return self.__class__.__name__+"@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"
class LocalApp(AnyApp): pass

#class CelsianApp(AnyApp): pass
#class MicressApp(AnyApp): pass
#class MmpraytracerApp(AnyApp): pass

# https://github.com/pahaz/sshtunnel
#import sshtunnel

from nose.tools import nottest

@nottest
class TestLocalApp(unittest.TestCase):
    jobname='TestLocalApp'
    hkey='mmp-secret-key'
    sshpwd='ssh-secret-key'
    # def __init__(self): super(TestLocalApp,self).__init__()
    def setUp(self):
        nshost,nsport='localhost',5000
        # 2000+i: ssh forwarder (forwards to localhost:3000+i); username testuser-2001 (number is port number), password is always mmp-secret-key
        # 3000+i: mupif application server
        # 4000+i: natport
        # 5000:   nameserver 

        # setup nameserver

        self.nsloop=multiprocessing.Process(target=Pyro4.naming.startNSloop,kwargs=dict(host=nshost,port=nsport,hmac=self.hkey))
        self.nsloop.start()
        time.sleep(2) # some time for nameserver to start

        # setup apps
        self.apps=LocalApp("/dev/null"), # CelsianApp("/dev/null"),MicressApp("/dev/null"),MmpraytracerApp("/dev/null")
        for i,app in enumerate(self.apps):
            # start "remote" servers (locally)
            print('Starting',app)
            PyroUtil.runAppServer(server='localhost',port=3000+i,nathost='localhost',natport=4000+i,nshost=nshost,nsport=nsport,nsname=PyroUtil.getNSAppName(self.jobname,app.__class__.__name__),hkey=self.hkey,app=app)
            # start ssh forwarder, between localhost and the remote server (those will be really run on remote machine externally accessible through ssh)
            # sshtunnel.SSHTunnelForwarder(ssh_address_or_host=('localhost',2000+i),ssh_username='testuser-%d'%(2000+i),ssh_password=self.sshpwd,local_bind_address=('127.0.0.1',4000+i),remote_bind_address=('127.0.0.1',3000+i))

    def tearDown(self):
        # terminate self.nsloop
        self.nsloop.terminate()
        self.nsloop.join()

    def testConnect(self):
        'Test connection through nameserver'
        ns=PyroUtil.connectNameServer('localhost',5000,'mmp-secret-key')
        print('Connected to nameserver')
        for i,app in enumerate(self.apps):
            # what is localport??
            #tunnel=PyroUtil.sshTunnel(remoteHost='localhost',userName='testuser-%d'%(2000+i),localPort=2000+i,remotePort=4000+i,sshClient='ssh',options='-oStrictHostKeyChecking=no',sshHost='')
            #print('Tunnel established')
            a=PyroUtil.connectApp(ns,PyroUtil.getNSAppName(self.jobname,app.__class__.__name__))
            print('Connected to App through Pyro')
            self.assert_(a)
            appsig=a.getApplicationSignature()
            print(appsig)
            tunnel.terminate()

if __name__=='__main__': unittest.main()
