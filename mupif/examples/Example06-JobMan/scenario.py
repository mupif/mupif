from builtins import str
import clientConfig as cConf
from mupif import *
import mupif

import time as timeTime
start = timeTime.time()

mupif.log.info('Timer started')

#if you wish to run no SSH tunnels, set to None
#sshContext = None
#sshContext = PyroUtil.SSHContext(userName=cConf.serverUserName, sshClient='manual', options=cConf.options)
sshContext = PyroUtil.SSHContext(userName=cConf.serverUserName, sshClient=cConf.sshClient, options=cConf.options)
print ("huhu:")
print (sshContext)



try:
    #locate nameserver
    ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)

    #connect to JobManager running on (remote) server and create a tunnel to it
    jobMan = PyroUtil.connectJobManager(ns, cConf.jobManName, sshContext)

    jobNatport = cConf.jobNatPorts.pop(0)
    app1 = PyroUtil.allocateApplicationWithJobManager( ns, jobMan, jobNatport, sshContext)

except Exception as e:
    mupif.log.exception(e)
else:
    if app1 is not None:
        appsig=app1.getApplicationSignature()
        mupif.log.info("Working application 1 on server " + appsig)

        val = Property.Property(1000, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
        app1.setProperty (val)
        app1.solveStep(None)
        retProp = app1.getProperty(PropertyID.PID_Demo_Value, 0.0)
        mupif.log.info("SUCCESSFULLY Received " + str(retProp.getValue()))
        mupif.log.info("Terminating " + str(app1.getURI()))
        #terminate
        mupif.log.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        mupif.log.debug("Connection to server failed, exiting")

    #allocate the second application, if necessary
    #PyroUtil.allocateNextApplication (ns, cConf.demoJobManRec, cConf.jobNatPorts.pop(0), appRec)
    #app2 = appRec.getApplication(1)
    #appsig=app2.getApplicationSignature()
    #logger.info("Working application 2 on server " + appsig)

finally:
    app1.terminate()
    mupif.log.info("Workflow terminated")


