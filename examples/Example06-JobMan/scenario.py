import conf
from mupif import *
import logging
logger = logging.getLogger()

import time as timeTime
start = timeTime.time()
logger.info('Timer started')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

#create tunnel to JobManager running on (remote) server
try:
    tunnelJobMan = PyroUtil.sshTunnel(remoteHost=conf.deamonHost, userName=conf.hostUserName, localPort=conf.jobManNatport, remotePort=conf.jobManPort, sshClient='ssh')
except Exception as e:
    logger.debug("Creating ssh tunnel for JobManager failed")
    logger.exception(e)
    sys.exit(e)
else:
    # locate remote jobManager on (remote) server
    jobMan = PyroUtil.connectApp(ns, conf.jobManName)
    if jobMan == None:
        logger.error('Can not connect to JobManager on server')

    #JobMan will assign a free port from a given list on the server (9091, 9092, 9093, 9094).
    #This port will be mapped to this computer's port 6000
    try:
        retRec = jobMan.allocateJob(PyroUtil.getUserInfo(), natPort=conf.jobNatPort)
        logger.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception as e:
        logger.info("jobMan.allocateJob() failed")
        logger.exception(e)
    #create tunnel to application's daemon running on (remote) server
    try:
        tunnelApp = PyroUtil.sshTunnel(remoteHost=conf.deamonHost, userName=conf.hostUserName, localPort=conf.jobNatPort, remotePort=retRec[2], sshClient='ssh')
    except Exception as e:
        logger.info("Creating ssh tunnel for application's daemon failed")
        logger.exception(e)
    else:
        logger.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

        timeTime.sleep(2)
        # connect to (remote) application, requests remote proxy
        app = PyroUtil.connectApp(ns, retRec[1])

        if app:
            appsig=app.getApplicationSignature()
            logger.info("Working application on server " + appsig)
        else:
            logger.debug("Connection to server failed, exiting")

        val = Property.Property(1000, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
        app.setProperty (val)
        app.solveStep(None)
        retProp = app.getProperty(PropertyID.PID_Demo_Value, 0.0)
        logger.info("Received " + str(retProp.getValue()))
        app.terminate();
        logger.info("Time consumed %f s" % (timeTime.time()-start))
        jobMan.terminateJob(retRec[1])
    finally:
        if tunnelApp: tunnelApp.terminate()
finally:
    if tunnelJobMan: tunnelJobMan.terminate()
