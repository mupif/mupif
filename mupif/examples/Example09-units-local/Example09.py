#!/usr/bin/env python
from builtins import str
import sys
sys.path.append('../../..')

from mupif import *
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ

class application1(Model.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self):
        super(application1,self).__init__()
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Velocity):
            return Property.ConstantProperty(self.value, PropertyID.PID_Velocity, ValueType.Scalar, 'm/s', time, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf('s').getValue()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1,'s')


time  = 0
timestepnumber=0
targetTime = 1.0 # 10 steps is enough


app1 = application1()

app1Metadata = {'Model.Model_ID' : 'Model ID-1234',
                'Model.Model_name' : 'Simple application storing calling time',
                'Model.Model_description' : 'Stores calling time'
               }

app1.initialize(metaData=app1Metadata)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep().inUnitsOf('s').getValue()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g"%(timestepnumber,time,dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, 's', timestepnumber)
    
    #solve problem 1
    app1.solveStep(istep)
    #request Concentration property from app1
    v = app1.getProperty(PropertyID.PID_Velocity, istep.getTime())
    
    #Create a PhysicalQuantity object 
    V = PQ.PhysicalQuantity(v.getValue(istep.getTime()), v.getUnits())

    velocity = V.inBaseUnits()
    log.debug(velocity)

    #can be converted in km/s?
    log.debug(V.isCompatible('km/s'))

    #can be converted in km?
    log.debug(V.isCompatible('km'))
    
    # convert in km/h
    V.convertToUnit('km/h') 
    log.debug(V)

    #give only the value
    value = float(str(V).split()[0])
    log.debug(value)

if (abs(value-3.6) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate();


