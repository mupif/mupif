# This script starts a client for Pyro5 on this machine with Application1
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import sys
sys.path.extend(['..', '../..'])
from mupif import *
import logging
log = logging.getLogger()

import mupif as mp


import threading
threading.current_thread().setName('ex02-main')


class Application1(mp.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, metadata={}):
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.

    def get(self, objectTypeID, time=None, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if objectTypeID == mp.DataID.PID_Time_step:
            return property.ConstantProperty(
                value=(self.value,), propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise apierror.APIError('Unknown DataID')

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf('s').getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return .1*mp.U.s

    def getAsssemblyTime(self, tstep):
        return tstep.getTime()


time = 0
timestepnumber = 0
targetTime = 1.0

# locate nameserver
ns = pyroutil.connectNameserver()

# application1 is local, create its instance
app1 = Application1()
# locate (remote) application2, request remote proxy
app2 = pyroutil.connectApp(ns, 'mupif/example02/app2')

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

app1.initialize(metadata=executionMetadata)
app2.initialize(metadata=executionMetadata)

prop = None
istep = None

while abs(time - targetTime) > 1.e-6:
    # determine critical time step
    dt2 = app2.getCriticalTimeStep().inUnitsOf(mp.U.s).getValue()
    dt = min(app1.getCriticalTimeStep().inUnitsOf(mp.U.s).getValue(), dt2)
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %d %f %f" % (timestepnumber, time, dt))
    # create a time step
    istep = mp.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mp.U.s, number=timestepnumber)

    try:
        # solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.get(mp.DataID.PID_Time_step, app2.getAssemblyTime(istep))
        app2.set(c)
        # app2.set(app1.get(DataID.PID_Time, app2.getAssemblyTime(istep)))
        # solve second sub-problem 
        app2.solveStep(istep)

        prop = app2.get(mp.DataID.PID_Time, istep.getTime())

        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f app1-time step %5.2f, app2-cummulative time %5.2f" % (
            atime.getValue(), c.getValue(atime)[0], prop.getValue(atime)[0]))

    except apierror.APIError as e:
        log.error("Following API error occurred: %s" % e)
        break

# prop = app2.get(DataID.PID_Time, istep.getTime())
# log.debug("Result: %f" % prop.getValue(istep.getTime()))

if prop is not None and istep is not None and abs(prop.getValue(istep.getTime())[0]-5.5) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate()
app2.terminate()
