import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 
#os.environ['PYRO_LOGLEVEL'] = 'DEBUG'
#os.environ['PYRO_LOGFILE'] = 'Pyro_log.txt' #overloads other logging output files

import logging
#put logging before Pyro4 module
logging.basicConfig(filename='mupif.pyro.log',filemode='w',datefmt="%Y-%m-%d %H:%M:%S",level=logging.DEBUG)
logging.getLogger('Pyro4').setLevel(logging.DEBUG)
logger = logging.getLogger('test.py')
logger.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler()) #display logging also on screen
from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
from mupif import PyroUtil
import time as timeTime
import Pyro4

sshtmode = 1
if (sshtmode == 0):
    from sshtunnel import SSHTunnelForwarder

    server = SSHTunnelForwarder(
        ssh_address=('mech.fsv.cvut.cz', 22),
        ssh_username="mmp",
        ssh_password="mmp2014mmp",
        remote_bind_address=('127.0.0.1', 44382),
        local_bind_address=('127.0.0.1', 5555))

    server.start()
    print (server)
    print("server.local_bind_port:%d "% server.local_bind_port)
    timeTime.sleep(0.1)
elif (sshtmode==1):
    #Windows tunnel using putty
    #tunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='mmp', localPort=5555, remotePort=44382, sshClient='putty', options='-i L:\.ssh\putty.ppk')
    #Linux tunnel using ssh
    tunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='mmp', localPort=5555, remotePort=44382, sshClient='ssh')

time  = 0
dt    = 1
expectedValue = 4.5

start = timeTime.time()
#locate nameserver
ns     = PyroUtil.connectNameServer('mech.fsv.cvut.cz', 9090)

# locate remote PingServer application, request remote proxy
serverApp = PyroUtil.connectApp (ns, 'Mupif.PingServerApplication')

#app2.__init__(None)

try:
    appsig=serverApp.getApplicationSignature()
    logger.info("Working application on server " + appsig)
except Exception as e:
    logger.debug("Connection to server failed, exiting")
    logger.exception(e)
    sys.exit(e)
    
logger.info("Generating test sequence ...")

for i in range (10):
    time = i
    timestepnumber = i
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)
    try:
        serverApp.setProperty (Property.Property(i, PropertyID.PID_Concentration, ValueType.Scalar, i, None, 0))
        serverApp.solveStep(istep)

    except APIError.APIError as e:
        logger.exception("Following API error occurred:" + e)
        break

logger.info("done")
prop = serverApp.getProperty(PropertyID.PID_CumulativeConcentration, i)
logger.info("Received " + str(prop.getValue()) + " expected " + str(expectedValue) )
if (prop.getValue() == expectedValue):
    logger.info("Test PASSED")
else:
    logger.info("Test FAILED")

serverApp.terminate();
logger.info("Time consumed %f s" % (timeTime.time()-start))
logger.info("Ping test finished")

if (sshtmode==0):
    server.terminate()
elif (sshtmode ==1):
    tunnel.terminate()

