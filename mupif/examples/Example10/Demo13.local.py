#!/usr/bin/env python
from __future__ import print_function

import sys
sys.path.append('../../..')
import demoapp
import meshgen
from mupif import *

time  = 0
timestepnumber = 0
targetTime = 10.0

app1 = demoapp.thermal_nonstat('inputT13.in','.')
app2 = demoapp.mechanical('inputM13.in', '.')

while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = app1.getCriticalTimeStep()
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g"%(timestepnumber,time,dt))
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request Temperature from app1
        f = app1.getField(FieldID.FID_Temperature, istep)
        data = f.field2VTKData().tofile('T_%s'%str(timestepnumber))
        print ("T(l/2)=", f.evaluate((2.5,0.2,0.0)))

        app2.setField(f)
        sol = app2.solveStep(istep) 
        f = app2.getField(FieldID.FID_Displacement, istep)
        print ("D(l,1)=", f.evaluate((5.0,1.0,0.0)))
        data = f.field2VTKData().tofile('D_%s'%str(timestepnumber))

    except APIError.APIError as e:
        mupif.log.error("Following API error occurred:",e)
        break
# terminate
app1.terminate();


