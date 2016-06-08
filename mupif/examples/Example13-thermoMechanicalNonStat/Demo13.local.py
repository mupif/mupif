#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.append('../../..')
from mupif import *
from mupif import logger
# Import module Example10/demoapp.py
sys.path.append('../Example10')
import demoapp

time  = 0.
dt = 0.
timestepnumber = 0
targetTime = 10.0

thermal = demoapp.thermal_nonstat('inputT13.in','.')
mechanical = demoapp.mechanical('inputM13.in', '.')

while (abs(time - targetTime) > 1.e-6):

    logger.debug("Step: %g %g %g"%(timestepnumber,time,dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        # solve problem 1
        thermal.solveStep(istep)
        # request Temperature from thermal
        f = thermal.getField(FieldID.FID_Temperature, istep.getTime())
        #print ("T(l/2)=", f.evaluate((2.5,0.2,0.0)))
        data = f.field2VTKData().tofile('T_%s'%str(timestepnumber))

        mechanical.setField(f)
        sol = mechanical.solveStep(istep) 
        f = mechanical.getField(FieldID.FID_Displacement, istep.getTime())
        #print ("D(l,1)=", f.evaluate((5.0,1.0,0.0)))
        data = f.field2VTKData().tofile('M_%s'%str(timestepnumber))

        # finish step
        thermal.finishStep(istep)
        mechanical.finishStep(istep)

        # determine critical time step
        dt = min (thermal.getCriticalTimeStep(), mechanical.getCriticalTimeStep())

        # update time
        time = time+dt
        if (time > targetTime):
            # make sure we reach targetTime at the end
            time = targetTime
        timestepnumber = timestepnumber+1

    except APIError.APIError as e:
        logger.error("Following API error occurred:",e)
        break

# terminate
thermal.terminate();
mechanical.terminate();

