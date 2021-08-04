#!/usr/bin/env python
import sys
import logging
sys.path.append('../..')
import mupif as mp

log = logging.getLogger()


class Application1(mp.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Simple application returning simulation time',
            'ID': 'N/A',
            'Description': 'Returns simulation time',
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
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Simulation time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.

    def initialize(self, workdir='', metadata={}, validateMetaData=True):
        super().initialize(workdir, metadata, validateMetaData)

    def get(self, objectTypeID, time=None, objectID=0):
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=(self.value,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, objectID=0)
        else:
            raise mp.APIError('Unknown property ID')
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf(mp.U.s).getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return .1*mp.U.s


time = 0
timestepnumber = 0
targetTime = 1.0  # 10 steps is enough

app1 = Application1()

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metadata=executionMetadata)

value = 0.
while abs(time - targetTime) > 1.e-6:

    # determine critical time step
    dt = app1.getCriticalTimeStep().inUnitsOf(mp.U.s).getValue()
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g" % (timestepnumber, time, dt))
    # create a time step
    istep = mp.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mp.U.s, number=timestepnumber)
    
    # solve problem 1
    app1.solveStep(istep)
    # request Concentration property from app1
    v = app1.get(mp.DataID.PID_Time, istep.getTime())
    
    # Create a PhysicalQuantity object
    V = mp.units.Quantity(value=v.getValue(istep.getTime())[0], unit=v.getUnit())

    val = V.inBaseUnits()
    log.debug(val)

    # can be converted in min?
    log.debug(V.isCompatible('min'))

    # can be converted in m?
    log.debug(V.isCompatible('m'))
    
    # convert to min
    V2 = V.inUnitsOf('min')
    log.debug(V2)

    # give only the value
    value = V2.getValue()
    log.debug(value)

if abs(value-targetTime/60.) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate()
