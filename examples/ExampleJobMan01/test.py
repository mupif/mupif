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
import getopt
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger()
#ssh flag (se to tru if ssh tunnel need to be established)
ssh = False

#parse arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:r:")
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    print ("test.py -p port -r repeat")
    sys.exit(2)

repeat = 1000
port = -1 # the port will be same as the ane assigned by the jobmanager
for o, a in opts:
    if o in ("-p", "--port"):
        port = int(a)
    elif o in ("-r"):
        repeat = int(a)
    else:
        assert False, "unhandled option"


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
    retRec = jobMan.allocateJob(PyroUtil.getUserInfo(), port)
    print retRec
except:
    logger.info("jobMan.allocateJob() failed")
    raise
    exit(1)

#TODO: establist ssh commection to port, how to select local port? this is the one as used 
if ssh:
    apptunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='bp', localPort=port, remotePort=retRec[2], sshClient='ssh')


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



