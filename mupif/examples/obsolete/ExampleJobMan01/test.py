#!/usr/bin/env python
from builtins import str
import sys

#import common configuration file
sys.path.append('..')
import clientConfig as cConf

from mupif import *
import time as timeTime
import getopt
import logging
logger = logging.getLogger()

start = timeTime.time()
logger.info('Timer started')
import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)

#localize JobManager running on (remote) server and create a tunnel to it
#allocate the first application app1
solverAppRec = None
try:
    solverJobManRec = (cConf.serverPort, cConf.serverNatport, cConf.server, cConf.serverUserName, cConf.jobManName)
    solverAppRec = PyroUtil.allocateApplicationWithJobManager( ns, solverJobManRec, cConf.jobNatPorts.pop(0), cConf.sshClient, cConf.options, cConf.sshHost )
    app = solverAppRec.getApplication()

except Exception as e:
    logger.exception(e)
else:
    if ((app is not None)):
        solverSignature=app.getApplicationSignature()
        logger.info("Working solver on server " + solverSignature)

        val = Property.ConstantProperty(10, PropertyID.PID_Demo_Value, ValueType.ValueType.Scalar, PQ.getDimensionlessUnit(), '0 s', 0)
        app.setProperty (val)
        tstep=TimeStep(0., 1., 1., timeUnits)
        app.solveStep(tstep)
        retProp = app.getProperty(PropertyID.PID_Demo_Value, tstep.getTime())
        logger.info("Received " + str(retProp.getValue()))
        #terminate
        logger.info("Time consumed %f s" % (timeTime.time()-start))

        if (abs(retProp.getValue()-10.0) <= 1.e-4):
            print ("Test OK")
        else:
            print ("Test FAILED")
            sys.exit(1)

    else:
        logger.debug("Connection to server failed, exiting")
        print ("Test FAILED")
        sys.exit(1)

finally:
    if solverAppRec: solverAppRec.terminateAll()
