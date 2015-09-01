#!/usr/bin/env python

from __future__ import print_function
import sys
sys.path.append('../../..')

from mupif.Physics.PhysicalQuantities import PhysicalQuantity as PQ

from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType

class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Velocity):
            return Property.Property(self.value, PropertyID.PID_Velocity, ValueType.Scalar, time, 'm/s', 0)
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


app1 = application1(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    print ("Step: ", timestepnumber, time, dt)
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)
    
    #solve problem 1
    app1.solveStep(istep)
    #request Concentration property from app1
    v = app1.getProperty(PropertyID.PID_Velocity, istep)
    
    #Create a PhysicalQuantity object 
    V = PQ(v.getValue(), v.getUnits())

    velocity = V.inBaseUnits()
    print(velocity)

    #can be converted in km/s?
    print(V.isCompatible('km/s'))

    #can be converted in km?
    print(V.isCompatible('km'))
    
    # convert in km/h
    V.convertToUnit('km/h') 
    print(V)

    #give only the value
    value = float(str(V).split()[0])
    print(value)

    # terminate
app1.terminate();


