from builtins import str
from builtins import range
import os,sys
sys.path.append('..')
import conf as cfg
from mupif import *
import time as timeTime
import logging
log = logging.getLogger()

#if you wish to run no SSH tunnels, set to None
#sshContext = None
sshContext = PyroUtil.SSHContext(userName=cfg.serverUserName, sshClient=cfg.sshClient, options=cfg.options)


#use numerical IP values only (not names, sometimes they do not work)
try:
    time  = 0
    dt    = 1
    expectedValue = 4.5

    start = timeTime.time()
    #locate nameserver
    ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

    # locate remote PingServer application, request remote proxy
    # tunnel created on the fly and terminated with application
    serverApp = PyroUtil.connectApp(ns, cfg.appName, sshContext)

    try:
        appsig=serverApp.getApplicationSignature()
        log.debug("Working application on server " + appsig)
    except Exception as e:
        log.error("Connection to server failed, exiting")
        log.exception(e)
        sys.exit(1)

    log.info("Generating test sequence ...")

    for i in range (10):
        time = i
        timestepnumber = i
        # create a time step
        istep = TimeStep.TimeStep(time, dt, timestepnumber)
        try:
            serverApp.setProperty (Property.Property(i, PropertyID.PID_Concentration, ValueType.Scalar, i, None, 0))
            serverApp.solveStep(istep)

        except APIError.APIError as e:
            log.exception("Following API error occurred:" + e)
            break

    log.debug("Done")
    prop = serverApp.getProperty(PropertyID.PID_CumulativeConcentration, i)
    log.debug("Received " + str(prop.getValue()) + " expected " + str(expectedValue) )
    if (prop.getValue() == expectedValue):
        log.info("Test PASSED")
    else:
        log.error("Test FAILED")
        sys.exit(1)

    serverApp.terminate();
    log.debug("Time consumed %f s" % (timeTime.time()-start))
    log.debug("Ping test finished")


finally:
    log.info("Test Terminated")
