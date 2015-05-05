import clientConfig as conf
from mupif import *
import logging
logger = logging.getLogger()

import time as timeTime
start = timeTime.time()
logger.info('Timer started')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

jobManTunnel = None
appTunnel = None
#create tunnel to JobManager running on (remote) server
try:
    (jobMan, jobManTunnel) = PyroUtil.connectJobManager (ns, conf.demoJobManRec)
    (app, appJobID, appTunnel) = PyroUtil.allocateApplicationWithJobManager (ns, conf.demoJobManRec, jobMan, conf.jobNatPorts.pop())
except Exception as e:
    logger.exception(e)
    if jobManTunnel: jobManTunnel.terminate()
    if appTunnel: appTunnel.terminate()
else:

    if app:
        appsig=app.getApplicationSignature()
        logger.info("Working application on server " + appsig)
    else:
        logger.debug("Connection to server failed, exiting")
        if appTunnel: appTunnel.terminate()

    val = Property.Property(1000, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
    app.setProperty (val)
    app.solveStep(None)
    retProp = app.getProperty(PropertyID.PID_Demo_Value, 0.0)
    logger.info("Received " + str(retProp.getValue()))
    
    logger.info("Terminating " + str(app.getURI()))
    app.terminate();
    jobMan.terminateJob(appJobID)

    if appTunnel: appTunnel.terminate()
    if jobManTunnel: jobManTunnel.terminate()

    logger.info("Time consumed %f s" % (timeTime.time()-start))

