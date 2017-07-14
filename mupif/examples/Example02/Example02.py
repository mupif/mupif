# This script starts a client for Pyro4 on this machine with Application1
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import sys
sys.path.append('..')
sys.path.append('../../..')
from mupif import *
import logging
log = logging.getLogger()

import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)


class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        super(application1, self).__init__(file)
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.Property(self.value, PropertyID.PID_Concentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1

time = 0
timestepnumber=0
targetTime = 1.3

sshContext = None
if mode==2: #just print out how to set up a SSH tunnel
    sshContext =  PyroUtil.SSHContext(userName=cfg.serverUserName, sshClient='ssh', options=cfg.options)
    #PyroUtil.sshTunnel(cfg.server, cfg.serverUserName, cfg.serverNatport, cfg.serverPort, 'ssh', cfg.options)

#locate nameserver
ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

# application1 is local, create its instance
app1 = application1(None)
# application2 is remote, request remote proxy
app2=PyroUtil.connectApp(ns, cfg.appName, cfg.hkey, sshContext)

while (abs(time -targetTime) > 1.e-6):
    #determine critical time step
    dt2 = app2.getCriticalTimeStep()
    dt = min(app1.getCriticalTimeStep(), dt2)
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %d %f %f" % (timestepnumber, time, dt) )
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request temperature field from app1
        c = app1.getProperty(PropertyID.PID_Concentration, istep)
        # register temperature field in app2
        app2.setProperty (c)
        # solve second sub-problem 
        app2.solveStep(istep)

    except APIError.APIError as e:
        log.error("Following API error occurred: %s" % e )
        break

prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep)
log.debug("Result: %f" % prop.getValue() )

if (abs(prop.getValue()-0.700000) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate();
app2.terminate();
