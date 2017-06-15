#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.append('../../..')
from mupif import *
sys.path.append('..')
import conf_vpn as cfg

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Locate thermal server
thermal = PyroUtil.connectApp(ns, 'thermal')
#Locate mechanical server
mechanical = PyroUtil.connectApp(ns, 'mechanical')

time  = 0.
dt = 0.
timestepnumber = 0
targetTime = 10.0

while (abs(time - targetTime) > 1.e-6):

    log.debug("Step: %g %g %g"%(timestepnumber,time,dt))
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
        log.error("Following API error occurred:",e)
        break

# terminate
thermal.terminate();
mechanical.terminate();

