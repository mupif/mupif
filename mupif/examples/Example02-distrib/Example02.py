# This script starts a client for Pyro4 on this machine with Application1
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import sys
sys.path.extend(['..','../../..'])
from mupif import *
import logging
log = logging.getLogger()

import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)

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
            return Property.ConstantProperty(self.value, PropertyID.PID_Concentration, ValueType.Scalar, 'kg/m**3', time, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf(timeUnits).getValue()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')

time = 0
timestepnumber=0
targetTime = 0.6

sshContext = None
if mode==1: #just print out how to set up a SSH tunnel
    sshContext =  PyroUtil.SSHContext(userName=cfg.serverUserName, sshClient=cfg.sshClient, options=cfg.options)
    #PyroUtil.sshTunnel(cfg.server, cfg.serverUserName, cfg.serverNatport, cfg.serverPort, cfg.sshClient, cfg.options)

#locate nameserver
ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

# application1 is local, create its instance
app1 = application1(None)
# locate (remote) application2, request remote proxy
app2=PyroUtil.connectApp(ns, cfg.appName, cfg.hkey, sshContext)

try:
    appsig=app2.getApplicationSignature()
    log.debug("Working application2 on server " + appsig)
except Exception as e:
    log.error("Connection to server failed, exiting")
    log.exception(e)
    sys.exit(1)

while (abs(time - targetTime) > 1.e-6):
    #determine critical time step
    dt2 = app2.getCriticalTimeStep().inUnitsOf(timeUnits).getValue()
    dt = min(app1.getCriticalTimeStep().inUnitsOf(timeUnits).getValue(), dt2)
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %d %f %f" % (timestepnumber, time, dt) )
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, timeUnits, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request concentration from app1
        c = app1.getProperty(PropertyID.PID_Concentration, istep.getTime())
        # register concentration in app2
        app2.setProperty (c)
        # solve second sub-problem 
        app2.solveStep(istep)

    except APIError.APIError as e:
        log.error("Following API error occurred: %s" % e )
        break

prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep.getTime())
log.debug("Result: %f" % prop.getValue(istep.getTime()) )

if (abs(prop.getValue(istep.getTime())-0.35) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate();
app2.terminate();
