#!/usr/bin/env python

import sys
sys.path.append('../..')
sys.path.append('.')
import clientConfig as conf
from mupif import *

import DemoApplication

import time as timeTime
import getopt
import logging
logger = logging.getLogger()

#ssh flag (True if a ssh tunnel needs to be established)
ssh = False

#parse arguments
if len(sys.argv) > 1:
    repeat = int(sys.argv[1])
else:
    repeat = 1000

try:
    opts, args = getopt.getopt(sys.argv[1:], "p:r:")
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    print ("test.py -p port -r repeat")
    sys.exit(2)

port = -1 # the port will be assigned by the jobManager
for o, a in opts:
    if o in ("-p", "--port"):
        port = int(a)
    elif o in ("-r"):
        repeat = int(a)
    else:
        assert False, "unhandled option"

#locate the nameServer
ns = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")
#extablish secure ssh tunnel connection
if ssh:
    tunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='bp', localPort=5353, remotePort=44382, sshClient='ssh')


start = timeTime.time()
# locate remote jobManager application, request remote proxy
jobMan = PyroUtil.connectApp(ns, 'Mupif.JobManager@demo')

try:
    retRec = jobMan.allocateJob(PyroUtil.getUserInfo(), port)
    print retRec
except:
    logger.info("jobMan.allocateJob() failed")
    raise
    exit(1)

#TODO: establish a ssh commection to port, how to select local port? this is the one as used 
if ssh:
    apptunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='bp', localPort=port, remotePort=retRec[2], sshClient='ssh')


logger.info("Connecting to " + retRec[1] + str(retRec[2]))
# connect to applications, request remote proxy
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
