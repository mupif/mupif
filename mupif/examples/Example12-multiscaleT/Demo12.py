import os,sys
sys.path.append('..')
import conf as cfg
from mupif import *
import mupif

#import module Example10/demoapp.py
sys.path.append('../Example10')
import demoapp
import logging
logger = logging.getLogger()

import time as timeTime
start = timeTime.time()
logger.info('Timer started')

tunnel = None
try:#tunnel must be closed at the end, otherwise bound socket may persist on system
    tunnel = PyroUtil.sshTunnel(cfg.server, cfg.serverUserName, cfg.serverNatport, cfg.serverPort, cfg.sshClient, cfg.options)

    #locate a nameserver
    ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
    # locate remote thermal server
    thermalMicro = PyroUtil.connectApp(ns, 'thermalMicro')
    thermalMicroSignature = thermalMicro.getApplicationSignature()
    logger.info("Working thermal solver on server " + thermalMicroSignature )
    logger.info("Solving thermal problem on server " + thermalMicroSignature )
    thermalMicro.solveStep(None)
    thermalMicroField = thermalMicro.getField(FieldID.FID_Temperature, 0.0)
    thermalMicroField.field2VTKData().tofile('thermalMicroField')

    #print (thermalSolver)

    #try:
        #appsig=thermalSolver.getApplicationSignature()
        #mupif.log.debug("Working application on server " + appsig)
    #except Exception as e:
            #mupif.log.error("Connection to server failed, exiting")
            #mupif.log.exception(e)
            #sys.exit(1)

finally:
    mupif.log.debug("Closing ssh tunnel")
    if tunnel:
        tunnel.terminate()

