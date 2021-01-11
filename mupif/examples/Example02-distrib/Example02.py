# This script starts a client for Pyro4 on this machine with Application1
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import logging
log = logging.getLogger()

import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)

import mupif.physics.physicalquantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1., [0, 0, 1, 0, 0, 0, 0, 0, 0])


class application1(model.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, metaData={}):
        MD = {
            'Name': 'Simple application storing time steps',
            'ID': 'N/A',
            'Description': 'Cummulates time steps',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Python script',
                'Language': 'Python3',
                'License': 'LGPL',
                'Creator': 'Borek',
                'Version_date': '02/2019',
                'Type': 'Summator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'High',
                'Sensitivity': 'High',
                'Complexity': 'Low',
                'Robustness': 'High'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated'}]
        }
        super(application1, self).__init__(metaData=MD)
        self.updateMetadata(metaData)
        self.value = 0.

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == PropertyID.PID_Time_step:
            return property.ConstantProperty(
                (self.value,), PropertyID.PID_Time_step, ValueType.Scalar, 's', time, metaData=md)
        else:
            raise apierror.APIError('Unknown property ID')

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        super(application1, self).initialize(file, workdir, metaData, validateMetaData, **kwargs)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf('s').getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')

    def getAsssemblyTime(self, tstep):
        return tstep.getTime()


time = 0
timestepnumber = 0
targetTime = 1.0

sshContext = None
if mode == 1:  # just print out how to set up a SSH tunnel
    sshContext = pyroutil.SSHContext(userName=cfg.serverUserName, sshClient=cfg.sshClient, options=cfg.options)
    # pyroutil.sshTunnel(cfg.server, cfg.serverUserName, cfg.serverNatport, cfg.serverPort, cfg.sshClient, cfg.options)

# locate nameserver
ns = pyroutil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

# application1 is local, create its instance
app1 = application1()
# locate (remote) application2, request remote proxy
app2 = pyroutil.connectApp(ns, cfg.appName, cfg.hkey, sshContext)

try:
    appsig = app2.getApplicationSignature()
    log.debug("Working application2 on server " + appsig)
except Exception as e:
    log.error("Connection to server failed, exiting")
    log.exception(e)
    sys.exit(1)

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metaData=executionMetadata)
app2.initialize(metaData=executionMetadata)

prop = None
istep = None

while abs(time - targetTime) > 1.e-6:
    # determine critical time step
    dt2 = app2.getCriticalTimeStep().inUnitsOf(timeUnits).getValue()
    dt = min(app1.getCriticalTimeStep().inUnitsOf(timeUnits).getValue(), dt2)
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %d %f %f" % (timestepnumber, time, dt))
    # create a time step
    istep = timestep.TimeStep(time, dt, targetTime, timeUnits, timestepnumber)

    try:
        # solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.getProperty(PropertyID.PID_Time_step, app2.getAssemblyTime(istep))
        app2.setProperty(c)
        # app2.setProperty(app1.getProperty(PropertyID.PID_Time, app2.getAssemblyTime(istep)))
        # solve second sub-problem 
        app2.solveStep(istep)

        prop = app2.getProperty(PropertyID.PID_Time, istep.getTime())

        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f app1-time step %5.2f, app2-cummulative time %5.2f" % (
            atime.getValue(), c.getValue(atime)[0], prop.getValue(atime)[0]))

    except apierror.APIError as e:
        log.error("Following API error occurred: %s" % e)
        break

# prop = app2.getProperty(PropertyID.PID_Time, istep.getTime())
# log.debug("Result: %f" % prop.getValue(istep.getTime()))

if prop is not None and istep is not None and abs(prop.getValue(istep.getTime())[0]-5.5) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate()
app2.terminate()
