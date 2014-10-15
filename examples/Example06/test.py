import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 
os.environ['PYRO_LOGLEVEL'] = 'DEBUG'
os.environ['PYRO_LOGFILE'] = 'Pyro_log.txt'

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
    tunnel = PyroUtil.sshTunnel(remoteHost='mech.fsv.cvut.cz', userName='mmp', localPort=5555, remotePort=44382)

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
    print ("Connected to ", appsig)
except Exception as e:
    print ("Connection to server failed")
    sys.exit(e)
    

print ("Generating test sequence ...")

for i in range (10):
    time = i
    timestepnumber = i
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)
    try:
        serverApp.setProperty (Property.Property(i, PropertyID.PID_Concentration, ValueType.Scalar, i, None, 0))
        serverApp.solveStep(istep)

    except APIError.APIError as e:
        print ("Following API error occurred:",e)
        break

print ("done")
prop = serverApp.getProperty(PropertyID.PID_CumulativeConcentration, i)
print ("Received ", prop.getValue(), " expected ", expectedValue)
if (prop.getValue() == expectedValue):
    print ("Test PASSED")
else:
    print ("Test FAILED")

serverApp.terminate();
print ("Time consumed %f s" % (timeTime.time()-start))
print ("Ping test finished")

if (sshtmode==0):
    server.terminate()
elif (sshtmode ==1):
    tunnel.terminate()


