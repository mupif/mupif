import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 

import logging
#put logging before Pyro4 module
logging.basicConfig(filename='mupif.pyro.log',filemode='w',datefmt="%Y-%m-%d %H:%M:%S",level=logging.DEBUG)
logging.getLogger('Pyro4').setLevel(logging.DEBUG)
logger = logging.getLogger('test.py')
logger.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler()) #display logging also on screen

from mupif import Application
from mupif import APIError
from mupif import PyroUtil
import time as timeTime
import conf

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}


start = timeTime.time()
#locate nameserver
ns     = PyroUtil.connectNameServer('mech.fsv.cvut.cz', 9090)

for apprecord in conf.apps:
    logging.info("Trying to connect to server " + str(apprecord[conf.appIndx_Name]))
    tunnel = PyroUtil.sshTunnel(remoteHost=apprecord[conf.appIndx_ServerName], userName=apprecord[conf.appIndx_UserName], 
                                localPort=apprecord[conf.appIndx_NATPort], remotePort=apprecord[conf.appIndx_RemotePort],
                                sshClient=apprecord[conf.appIndx_SshClient])

    # connect to individual applications
    app = PyroUtil.connectApp(ns, PyroUtil.getNSAppName(conf.jobname, apprecord[conf.appIndx_Name]))
    if app:
        appsig=app.getApplicationSignature()
        logging.info("Successfully connected to " + appsig)
        logging.info("Time since the beginning of ping test consumed %f s" % (timeTime.time()-start) )
    else:
        logging.error("Unable to connect to " + str(apprecord[conf.appIndx_Name]) )
    if tunnel:
        tunnel.terminate()

print ("Total time consumed %f s" % (timeTime.time()-start))
print ("Ping test finished")
