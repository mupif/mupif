import sys
sys.path.append('../..')
import os

import logging
logging.basicConfig(filename='scenario.log',filemode='w',level=logging.DEBUG)
logger = logging.getLogger('scenario')
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

import Pyro4
from mupif import Application
from mupif import APIError
from mupif import PyroUtil
import time as timeTime

start = timeTime.time()

#locate nameserver
ns = PyroUtil.connectNameServer(nshost='147.32.130.137', nsport=9090, hkey='mmp-secret-key')

#create tunnel to JobManager running on (remote) server
try:
    tunnelJobMan = PyroUtil.sshTunnel(remoteHost='localhost', userName='smilauer', localPort=5555, remotePort=44361, sshClient='ssh')

    # locate remote jobManager on (remote) server
    jobMan = PyroUtil.connectApp(ns, 'Mupif.JobManager@demo')
    if jobMan == None:
        logger.error('Can not connect to JobManager on server')

    #JobMan will assign a free port from a given list on the server (9091, 9092, 9093, 9094). 
    #This port will be mapped to this computer's port 6000
    try:
        retRec = jobMan.allocateJob(PyroUtil.getUserInfo(), natPort=6000)
        logger.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception as e:
        logger.info("jobMan.allocateJob() failed")
        logger.exception(e)

    #create tunnel to application's daemon running on (remote) server
    tunnelApp = PyroUtil.sshTunnel(remoteHost='localhost', userName='smilauer', localPort=6000, remotePort=44382, sshClient='ssh')

    logger.info("Connecting to " + retRec[1] + " " + str(retRec[2]))
    # connect to (remote) application, requests remote proxy
    app = PyroUtil.connectApp(ns, retRec[1])

    if app:
        appsig=app.getApplicationSignature()
        logger.info("Working application on server " + appsig)
    else:
        logger.debug("Connection to server failed, exiting")


    
    app.terminate();
    logger.info("Time consumed %f s" % (timeTime.time()-start))
    
    if tunnelApp: tunnelApp.terminate()

except Exception as e:
    logger.debug("Creating ssh tunnel failed")
    logger.exception(e)
    sys.exit(e)

finally:
    if tunnelJobMan: tunnelJobMan.terminate()

