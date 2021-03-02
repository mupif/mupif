import unittest
import sys, multiprocessing, time, os
import unittest,sys
import socket
sys.path.append('../..')

import mupif
import Pyro5

Pyro5.config.SERIALIZER = "serpent"
# Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
# Pyro5.config.SERIALIZERS_ACCEPTED = {'serpent'}
Pyro5.config.SERVERTYPE = "multiplex"

from mupif import pyroutil
@Pyro5.api.expose
class AnyApp(mupif.model.Model):
    def __init__(self,f): super(AnyApp,self).__init__(f)
    def getApplicationSignature(self): return self.__class__.__name__+"@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"
@Pyro5.api.expose
class LocalApp(AnyApp): 
    def getApplicationSignature(self): 
        return "Hello from LocalApp"

#class CelsianApp(AnyApp): pass
#class MicressApp(AnyApp): pass
#class MmpraytracerApp(AnyApp): pass

# https://github.com/pahaz/sshtunnel
#import sshtunnel

from nose.tools import nottest

@nottest
class TestLocalApp(unittest.TestCase):
    jobname='TestLocalApp'
    # hkey='mupif-secret-key'
    sshpwd='ssh-secret-key'
    # def __init__(self): super(TestLocalApp,self).__init__()
    def setUp(self):
        nshost,nsport='localhost',5000
        # 2000+i: ssh forwarder (forwards to localhost:3000+i); username testuser-2001 (number is port number), password is always mmp-secret-key
        # 3000+i: mupif application server
        # 4000+i: natport
        # 5000:   nameserver 

        # setup nameserver

        self.nsloop=multiprocessing.Process(target=Pyro5.nameserver.start_ns_loop,kwargs=dict(host=nshost,port=nsport))
        self.nsloop.start()
        time.sleep(2) # some time for nameserver to start

        # setup apps
        self.apps=(LocalApp(os.devnull),) # CelsianApp(os.devnull),MicressApp(os.devnull),MmpraytracerApp(os.devnull)
        for i,app in enumerate(self.apps):
            # start "remote" servers (locally)
            print('Starting',app)
            pyroutil.runAppServer(server='localhost',port=3000+i,nathost=None,natport=None,nshost=nshost,nsport=nsport,appName=pyroutil.getNSAppName(self.jobname,app.__class__.__name__),app=app)
            # start ssh forwarder, between localhost and the remote server (those will be really run on remote machine externally accessible through ssh)
            # sshtunnel.SSHTunnelForwarder(ssh_address_or_host=('localhost',2000+i),ssh_username='testuser-%d'%(2000+i),ssh_password=self.sshpwd,local_bind_address=('127.0.0.1',4000+i),remote_bind_address=('127.0.0.1',3000+i))
        print("Started all apps")

    def tearDown(self):
        # terminate self.nsloop
        self.nsloop.terminate()
        self.nsloop.join()

    def test_testConnect(self):
        'Test connection through nameserver'
        ns=pyroutil.connectNameServer('localhost',5000)
        print('Connected to nameserver')
        for i,app in enumerate(self.apps):
            # what is localport??
            #tunnel=pyroutil.SshTunnel(remoteHost='localhost',userName='testuser-%d'%(2000+i),localPort=2000+i,remotePort=4000+i,sshClient='ssh',options='-oStrictHostKeyChecking=no',sshHost='')
            #print('Tunnel established')
            a=pyroutil.connectApp(ns,pyroutil.getNSAppName(self.jobname,app.__class__.__name__))
            print('Connected to App through Pyro')
            self.assertTrue(a)
            appsig=a.getApplicationSignature()
            print(appsig)
            #tunnel.terminate()
            a.terminate()
            time.sleep(2) # some time for nameserver to start

if __name__=='__main__': unittest.main()
