from builtins import str
from builtins import range
import sys
sys.path.append('../../..')
import os

import logging
logger = logging.getLogger()

hkey = 'mmp-secret-key'

import Pyro4
from mupif import *
import time as timeTime
from config import Config
f = file('../config.cfg')
cfg = Config(f)


tunnel = None
#use numerical IP values only (not names, sometimes they do not work)
try:#tunnel must be closed at the end, otherwise bound socket may persist on system
    tunnel = PyroUtil.sshTunnel(cfg.server, cfg.serverUserName, cfg.serverNatport, cfg.serverPort, cfg.sshClient, cfg.options)

    time  = 0
    dt    = 1
    expectedValue = 4.5

    start = timeTime.time()
    #locate nameserver
    ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

    # locate remote PingServer application, request remote proxy
    serverApp = PyroUtil.connectApp(ns, cfg.appName)

    try:
        appsig=serverApp.getApplicationSignature()
        logger.info("Working application on server " + appsig)
    except Exception as e:
        logger.debug("Connection to server failed, exiting")
        logger.exception(e)
        sys.exit(e)

    logger.info("Generating test sequence ...")

    for i in range (10):
        time = i
        timestepnumber = i
        # create a time step
        istep = TimeStep.TimeStep(time, dt, timestepnumber)
        try:
            serverApp.setProperty (Property.Property(i, PropertyID.PID_Concentration, ValueType.Scalar, i, None, 0))
            serverApp.solveStep(istep)

        except APIError.APIError as e:
            logger.exception("Following API error occurred:" + e)
            break

    logger.info("Done")
    prop = serverApp.getProperty(PropertyID.PID_CumulativeConcentration, i)
    logger.info("Received " + str(prop.getValue()) + " expected " + str(expectedValue) )
    if (prop.getValue() == expectedValue):
        logger.info("Test PASSED")
    else:
        logger.info("Test FAILED")

    serverApp.terminate();
    logger.info("Time consumed %f s" % (timeTime.time()-start))
    logger.info("Ping test finished")

finally:
    logger.debug("Closing ssh tunnel")
    if tunnel:
        tunnel.terminate()

