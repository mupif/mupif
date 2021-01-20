import sys
sys.path.append('../../..')
from mupif import *
import logging
log = logging.getLogger()
import mupif.physics.physicalquantities as PQ


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
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated'}]
        }
        # calls constructor from Application module
        super(application1, self).__init__(metaData=MD)
        self.updateMetadata(metaData)
        self.value = 0.

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        super(application1, self).initialize(file, workdir, metaData, validateMetaData, **kwargs)

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

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = self.getAssemblyTime(tstep).inUnitsOf('s').getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')

    def getAssemblyTime(self, tstep):
        return tstep.getTime()


class application2(model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, metaData={}):
        MD = {
            'Name': 'Simple application cummulating time steps',
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
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super(application2, self).__init__(metaData=MD)
        self.updateMetadata(metaData)
        self.value = 0.0
        self.count = 0.0
        self.contrib = property.ConstantProperty(
            (0.,), PropertyID.PID_Time, ValueType.Scalar, 's', PQ.PhysicalQuantity(0., 's'))

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        super(application2, self).initialize(file, workdir, metaData, validateMetaData, **kwargs)

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == PropertyID.PID_Time:
            return property.ConstantProperty(
                (self.value,), PropertyID.PID_Time, ValueType.Scalar, 's', time, metaData=md)
        else:
            raise apierror.APIError('Unknown property ID')

    def setProperty(self, property, objectID=0):
        if property.getPropertyID() == PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = property
        else:
            raise apierror.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value = self.value+self.contrib.inUnitsOf('s').getValue(self.getAssemblyTime(tstep))[0]
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')

    def getAssemblyTime(self, tstep):
        return tstep.getTime()


time = 0
timestepnumber = 0
targetTime = 1.0

app1 = application1()
app2 = application2()

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metaData=executionMetadata)
# app1.printMetadata()

app1.toJSONFile('aa.json')
aa = mupifobject.MupifObject('aa.json')
# aa.printMetadata()

app2.initialize(metaData=executionMetadata)

prop = None
istep = None

while abs(time - targetTime) > 1.e-6:

    # determine critical time step
    dt = min(app1.getCriticalTimeStep().inUnitsOf('s').getValue(),
             app2.getCriticalTimeStep().inUnitsOf('s').getValue())
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    # create a time step
    istep = timestep.TimeStep(time, dt, targetTime, 's', timestepnumber)

    try:
        # solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.getProperty(PropertyID.PID_Time_step, app2.getAssemblyTime(istep))
        app2.setProperty(c)
        # solve second sub-problem 
        app2.solveStep(istep)

        prop = app2.getProperty(PropertyID.PID_Time, app2.getAssemblyTime(istep))
        # print (istep.getTime(), c, prop)
        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f app1-time step %5.2f, app2-cummulative time %5.2f" % (
            atime.getValue(), c.getValue(atime)[0], prop.getValue(atime)[0]))
        
    except apierror.APIError as e:
        log.error("mupif.APIError occurred:", e)
        log.error("Test FAILED")
        raise

if prop is not None and istep is not None and abs(prop.getValue(istep.getTime())[0]-5.5) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
# c.printMetadata()
# c.validateMetadata(dataID.DataSchema)
app1.terminate()
app2.terminate()
