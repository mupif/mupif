#!/usr/bin/env python
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

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
    istep = TimeStep.TimeStep(time, dt, time+dt, 's', timestepnumber)

    try:
        # solve problem 1
        thermal.solveStep(istep)
        # request Temperature from thermal
        print( istep.getTime(),  istep.getTime())
        
        f = thermal.getField(FieldID.FID_Temperature, mechanical.getAssemblyTime(istep))
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
        dt = min (thermal.getCriticalTimeStep().inUnitsOf('s').getValue(),
                  mechanical.getCriticalTimeStep().inUnitsOf('s').getValue())

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
log.info("Test OK")
