import sys
sys.path.append('../..')
import os
#os.environ["PYRO_LOGFILE"] = "pyro.log"
#os.environ["PYRO_LOGLEVEL"] = "DEBUG"

#set host running nameserver
nshost = '127.0.0.1'

from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
import Pyro4

Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x


class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.Property(self.value, PropertyID.PID_Concentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1

time  = 0
timestepnumber=0
targetTime = 10.0


daemon = Pyro4.Daemon()
ns     = Pyro4.locateNS(nshost, 9090)

# application1 is local, create its instance
app1 = application1(None)
# application2 is remote, request remote proxy
uri = ns.lookup("Mupif.application2")
print (uri)
app2 = Pyro4.Proxy(uri)


#app2.__init__(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = min(app1.getCriticalTimeStep(), app2.getCriticalTimeStep())
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    print ("Step: ", timestepnumber, time, dt)
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request temperature field from app1
        c = app1.getProperty(PropertyID.PID_Concentration, istep)
        # register temperature field in app2
        app2.setProperty (c)
        # solve second sub-problem 
        app2.solveStep(istep)

        
    except APIError.APIError as e:
        print ("Following API error occurred:",e)
        break

prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep)
print  ("Result: ", prop.getValue())
# terminate
app1.terminate();
app2.terminate();
