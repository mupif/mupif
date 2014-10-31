import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 
os.environ['PYRO_LOGLEVEL'] = 'DEBUG'
os.environ['PYRO_LOGFILE'] = 'Pyro_log.txt'
import time as timeTime

from mupif import Application
from mupif import APIError
from mupif import PyroUtil
import conf

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}

import logging
logging.getLogger().setLevel(logging.WARNING)
#logging.getLogger().setLevel(logging.DEBUG)


start = timeTime.time()
#locate nameserver
ns     = PyroUtil.connectNameServer('mech.fsv.cvut.cz', 9090)

for appname,apprecord in conf.apps.iteritems():
    tunnel = PyroUtil.sshTunnel(remoteHost=apprecord[conf.appIndx_ServerName], userName=apprecord[conf.appIndx_UserName], 
                                localPort=apprecord[conf.appIndx_NATPort], remotePort=apprecord[conf.appIndx_RemotePort])

    # connect to individual applications
    app = PyroUtil.connectApp(ns, PyroUtil.getNSAppName(conf.jobname, appname))

    appsig=app.getApplicationSignature()
    print ("Connected to "+ appsig)
    tunnel.terminate()

print ("done")
print ("Time consumed %f s" % (timeTime.time()-start))
print ("Ping test finished")



