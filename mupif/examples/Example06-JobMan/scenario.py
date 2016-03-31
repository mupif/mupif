from builtins import str
import clientConfig as cConf
from mupif import *
import logging
logger = logging.getLogger()

import time as timeTime
start = timeTime.time()
logger.info('Timer started')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)

#localize JobManager running on (remote) server and create a tunnel to it
#allocate the first application app1
#cConf.sshClient='manual'
try:
    appRec = PyroUtil.allocateApplicationWithJobManager( ns, cConf.solverJobManRec, cConf.jobNatPorts.pop(0), cConf.sshClient, cConf.options, cConf.sshHost )
    app1 = appRec.getApplication()
except Exception as e:
    logger.exception(e)
else:
    if app1 is not None:
        appsig=app1.getApplicationSignature()
        logger.info("Working application 1 on server " + appsig)

        val = Property.Property(1000, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
        app1.setProperty (val)
        app1.solveStep(None)
        retProp = app1.getProperty(PropertyID.PID_Demo_Value, 0.0)
        logger.info("SUCCESSFULLY Received " + str(retProp.getValue()))
        logger.info("Terminating " + str(app1.getURI()))
        #terminate
        logger.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        logger.debug("Connection to server failed, exiting")

    #allocate the second application, if necessary
    #PyroUtil.allocateNextApplication (ns, cConf.demoJobManRec, cConf.jobNatPorts.pop(0), appRec)
    #app2 = appRec.getApplication(1)
    #appsig=app2.getApplicationSignature()
    #logger.info("Working application 2 on server " + appsig)

finally:
    if appRec: appRec.terminateAll()


