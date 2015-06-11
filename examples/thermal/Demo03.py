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
try:
    appRec = PyroUtil.allocateApplicationWithJobManager( ns, cConf.demoJobManRec, cConf.jobNatPorts.pop(0), cConf.sshClient, cConf.options, cConf.sshHost )
    app1 = appRec.getApplication()
except Exception as e:
    logger.exception(e)
else:
    if app1 is not None:
        appsig=app1.getApplicationSignature()
        logger.info("Working application 1 on server " + appsig)

        logger.info("Uploading input file on server " + appsig)
        pf = appRec.getJobManager().getPyroFile(appRec.getJobID(), "input.in", 'w')
        PyroUtil.downloadPyroFile("input.in", pf)

        logger.info("Solving problem on server " + appsig)
        app1.solveStep(None)
        f = app1.getField(FieldID.FID_Temperature, 0.0)
        f.field2VTKData().tofile('example')
        #terminate
        logger.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        logger.debug("Connection to server failed, exiting")

finally:
    if appRec: appRec.terminateAll()



