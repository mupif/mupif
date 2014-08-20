import sys
sys.path.append('../..')

from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 

import Pyro4

time  = 0
dt    = 1
expectedValue = 4.5


daemon = Pyro4.Daemon()
ns     = Pyro4.locateNS('mech.fsv.cvut.cz', 9090)

# locate remote PingServer application, request remote proxy
uri = ns.lookup("Mupif.PingServerApplication")
print uri
serverApp = Pyro4.Proxy(uri)

#app2.__init__(None)

try:
    appsig=serverApp.getApplicationSignature()
    print "Connected to ", appsig
except Exception as e:
    print "Connection to server failed"
    sys.exit(e)
    

print "Generating test sequence ...",

for i in range (10):
    time = i
    timestepnumber = i
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)
    try:
        serverApp.setProperty (Property.Property(i, PropertyID.PID_Concentration, ValueType.Scalar, i, None, 0))
        serverApp.solveStep(istep)

    except APIError.APIError as e:
        print "Following API error occurred:",e
        break

print "done"
prop = serverApp.getProperty(PropertyID.PID_CumulativeConcentration, i)
print "Received ", prop.getValue(), " expected ", expectedValue
if (prop.getValue() == expectedValue):
    print "Test PASSED"
else:
    print "Test FAILED"

serverApp.terminate();
print "Ping test finished"
