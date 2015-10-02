# This script starts a client for Pyro4 on this machine with Application1
# Works with Pyro4 version 4.28
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz

from __future__ import print_function
import os, sys
sys.path.append('..')
import conf as cfg
from mupif import *
logger = cfg.logging.getLogger()

class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        super(application1, self).__init__(file)
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

#locate nameserver
ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

# application1 is local, create its instance
app1 = application1(None)
# application2 is remote, request remote proxy
app2=PyroUtil.connectApp(ns, cfg.appName)

while (abs(time -targetTime) > 1.e-6):
    #determine critical time step
    dt2 = app2.getCriticalTimeStep()
    dt = min(app1.getCriticalTimeStep(), dt2)
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    logger.info("Step: %d %f %f" % (timestepnumber, time, dt) )
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
        logger.error("Following API error occurred: %s" % e )
        break

prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep)
logger.info("Result: %f" % prop.getValue() )

if (abs(prop.getValue()-5.05) <= 1.e-4):
    print ("Test OK")
else:
    print ("Test FAILED")


# terminate
app1.terminate();
app2.terminate();
