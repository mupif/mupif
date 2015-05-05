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
    appRec = PyroUtil.allocateApplicationWithJobManager (ns, conf.demoJobManRec, conf.jobNatPorts.pop())
    app = appRec.getApplication()
except Exception as e:
    logger.exception(e)
    appRec.terminate()
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

    #terminate
    appRec.terminate()
    logger.info("Time consumed %f s" % (timeTime.time()-start))

