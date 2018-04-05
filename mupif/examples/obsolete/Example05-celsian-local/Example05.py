#!/usr/bin/env python

import sys
import Celsian
from mupif import *
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

time  = 0
timestepnumber = 0
targetTime = 0.1

app1 = Celsian.Celsian(None)

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep().inUnitsOf(timeUnits).getValue()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g"%(timestepnumber,time,dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, timeUnits, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request Temperature from app1
        field = app1.getField(FieldID.FID_Temperature, istep.getTime())

    except APIError.APIError as e:
        log.error("Following API error occurred: %s",e)
        break
# evaluate field at given point
position=(-1e-5, -1e-5, -1e-5)
value=field.evaluate(position)

#import datetime
#field.toHdf5(fileName='ex5dbg.h5',group=datetime.datetime.now().isoformat())

# Result
print ("Field value at position ", position, " is ", value)


if (abs(value.getValue()[0]-728.13) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)


# terminate
app1.terminate();


