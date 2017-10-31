from __future__ import print_function
from builtins import str
import sys
sys.path.append('../../..')
from mupif import *
import os
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])


class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        super(application1, self).__init__(file)
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.Property(self.value, PropertyID.PID_Concentration, ValueType.Scalar, time, 'kg/m**3', 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf(timeUnits).getValue()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1,'s')


class application3(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property using an external code
    """
    def __init__(self, file):
        # list storing all mapped values from the beginning
        super(application3, self).__init__(file)
        self.values = []
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            log.debug("Getting property name: %s with ID  %d" % (PropertyID.PID_CumulativeConcentration.name,PropertyID.PID_CumulativeConcentration.value) )
            # parse output of application3 
            f = open('app3.out', 'r')
            answer = float(f.readline())
            f.close()
            return Property.Property(answer, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, 'kg/m**3', 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.values.append(property.getValue())
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        f = open('app3.in', 'w')
        # process list of mapped values and store them into an external file 
        for val in self.values:
            f.write(str(val)+'\n')
        f.close()
        # execute external application to compute the average
        os.system("./application3")

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0,'s')

time  = 0
timestepnumber=0
targetTime = 10.0


app1 = application1(None)
app3 = application3(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = min(app1.getCriticalTimeStep().inUnitsOf(timeUnits).getValue(),
             app3.getCriticalTimeStep().inUnitsOf(timeUnits).getValue())
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g "%(timestepnumber,time,dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, timeUnits, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request Concentration property from app1
        c = app1.getProperty(PropertyID.PID_Concentration, istep.getTime())
        # register Concentration property in app3
        app3.setProperty (c)
        # solve second sub-problem 
        app3.solveStep(istep)

        
    except APIError.APIError as e:
        log.error("Following API error occurred:",e)
        break

prop = app3.getProperty(PropertyID.PID_CumulativeConcentration, istep.getTime())
log.debug("Result: "+str(prop.getValue()))

if (abs(prop.getValue()-5.05) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)


# terminate
app1.terminate();
app3.terminate();
