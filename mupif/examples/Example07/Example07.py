#!/usr/bin/env python
from __future__ import print_function

import sys
sys.path.append('../../..')
sys.path.append('.')
import Micress
import mupif
from mupif import FieldID
from mupif import TimeStep
from mupif import APIError

time  = 0
timestepnumber = 0
targetTime = 0.1

app1 = Micress.Micress(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    mupif.log.debug("Step: %g %g %g "%(timestepnumber, time, dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request Concentration property from app1
        field = app1.getField(FieldID.FID_Temperature, istep)

    except APIError.APIError as e:
        mupif.log.error("Following API error occurred:",e)
        sys.exit(1)
# evaluate field at given point
position=(0.0, 0.0, 0.0)
value=field.evaluate(position)

# Result
mupif.log.debug("Field value at position "+str(position)+" is "+str(value))
field.field2VTKData().tofile('example2')

if (abs(value[0]-22.0) <= 1.e-4):
    mupif.log.info("Test OK")
else:
    mupif.log.error("Test FAILED")
    sys.exit(1)


# terminate
app1.terminate();


