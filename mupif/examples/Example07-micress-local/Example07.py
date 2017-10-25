#!/usr/bin/env python
from __future__ import print_function

import sys
sys.path.append('../../..')
sys.path.append('.')
import Micress
from mupif import FieldID
from mupif import TimeStep
from mupif import APIError
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

time  = 0
timestepnumber = 0
targetTime = 0.1

app1 = Micress.Micress(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep().inUnitsOf(timeUnits).getValue()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g "%(timestepnumber, time, dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, timeUnits, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request Concentration property from app1
        field = app1.getField(FieldID.FID_Temperature, istep)
        #field.field2Image2D()

    except APIError.APIError as e:
        log.error("Following API error occurred:%s",e)
        sys.exit(1)
# evaluate field at given point
position=(0.0, 0.0, 0.0)
value=field.evaluate(position)

# Result
log.debug("Field value at position "+str(position)+" is "+str(value))
field.field2VTKData().tofile('example2')

if (abs(value[0]-22.0) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)


# terminate
app1.terminate();


