#!/usr/bin/env python
from builtins import str
import sys
import logging
sys.path.append('../..')

from mupif import *
import mupif.physics.physicalquantities as PQ

log = logging.getLogger()


class application1(model.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, metaData={}):
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time', 'Name': 'Simulation time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super(application1, self).__init__(metaData=MD)
        self.updateMetadata(metaData)
        self.value = 0.

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True):
        super(application1, self).initialize(file, workdir, metaData, validateMetaDatas)

    def getProperty(self, propID, time, objectID=0):
        if propID == PropertyID.PID_Time:
            return property.ConstantProperty((self.value,), PropertyID.PID_Time, ValueType.Scalar, 's', time, 0)
        else:
            raise apierror.APIError('Unknown property ID')
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf('s').getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')


time = 0
timestepnumber = 0
targetTime = 1.0  # 10 steps is enough

app1 = application1()

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metaData=executionMetadata)

value = 0.
while abs(time - targetTime) > 1.e-6:

    # determine critical time step
    dt = app1.getCriticalTimeStep().inUnitsOf('s').getValue()
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %g %g %g" % (timestepnumber, time, dt))
    # create a time step
    istep = timestep.TimeStep(time, dt, targetTime, 's', timestepnumber)
    
    # solve problem 1
    app1.solveStep(istep)
    # request Concentration property from app1
    v = app1.getProperty(PropertyID.PID_Time, istep.getTime())
    
    # Create a PhysicalQuantity object
    V = PQ.PhysicalQuantity(v.getValue(istep.getTime())[0], v.getUnits())

    val = V.inBaseUnits()
    log.debug(val)

    # can be converted in min?
    log.debug(V.isCompatible('min'))

    # can be converted in m?
    log.debug(V.isCompatible('m'))
    
    # convert to min
    V.convertToUnit('min')
    log.debug(V)

    # give only the value
    value = V.getValue()
    log.debug(value)

if abs(value-targetTime/60.) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate()


