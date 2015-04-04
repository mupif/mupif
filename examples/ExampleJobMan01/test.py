#!/usr/bin/env python


import sys
sys.path.append('../..')
sys.path.append('.')
import conf
from mupif import JobManager
from mupif import PyroUtil
from mupif import APIError
from mupif import Property
from mupif import PropertyID
from mupif import ValueType

import DemoApplication
import logging
import time as timeTime
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger()
#ssh flag (se to tru if ssh tunnel need to be established)
ssh = False



#parse arguments
if len(sys.argv) > 1:
    repeat = int(sys.argv[1])
else:
    repeat = 1000



#locate nameserver
ns     = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")
#extablish secure ssh tunnel connection
if ssh:
    tunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='bp', localPort=5353, remotePort=44382, sshClient='ssh')



start = timeTime.time()
# locate remote jobManager application, request remote proxy
jobMan = PyroUtil.connectApp(ns, 'Mupif.JobManager@demo')

# get application allocated
logger.info("Connected to " + jobMan.getApplicationSignature())
try:
    retRec = jobMan.allocateJob(PyroUtil.getUserInfo())
    print retRec
except:
    logger.info("jobMan.allocateJob() failed")
    raise
    exit(1)

#TODO: establist ssh commection to port, how to select local port? this is the one as used 
if ssh:
    apptunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='bp', localPort=9090, remotePort=retRec[2], sshClient='ssh')


logger.info("Connecting to " + retRec[1] + str(retRec[2]))
# connect to applications
app = PyroUtil.connectApp(ns, retRec[1])
                               
val = Property.Property(repeat, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
app.setProperty (val)

app.solveStep(None)
retProp = app.getProperty(PropertyID.PID_Demo_Value, 0.0)
logger.info("Received " + str(retProp.getValue()))
app.terminate()
jobMan.terminateJob(retRec[1])



logger.info("Time consumed %f s" % (timeTime.time()-start))
logger.info("Test finished")

if ssh:
    tunnel.terminate()



