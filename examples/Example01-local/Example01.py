import sys
import os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../..')

import mupif as mp

import logging
log=logging.getLogger(__name__)

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
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep", "ValueType": "Scalar"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', "ValueType": "Scalar"}]
        }
        # calls constructor from Application module
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if objectTypeID == mp.DataID.PID_Time_step:
            return mp.ConstantProperty(
                value=self.value, propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise mp.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = self.getAssemblyTime(tstep).inUnitsOf(mp.U.s).getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return .1*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()


class Application2(mp.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, metadata={}):
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep", "ValueType": "Scalar"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated', "ValueType": "Scalar"}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.0
        self.count = 0.0
        self.contrib = mp.ConstantProperty(
            value=0., propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0.*mp.U.s)

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir, metadata, validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(
                value=self.value, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise mp.APIError('Unknown property ID')

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mp.DataID.PID_Time_step:
                # remember the mapped value
                self.contrib = obj
            else:
                raise mp.APIError('Unknown DataID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value = self.value+self.contrib.inUnitsOf(mp.U.s).getValue(self.getAssemblyTime(tstep))
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()


time = 0
timestepnumber = 0
targetTime = 1.0

app1 = Application1()
app2 = Application2()

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metadata=executionMetadata)
# app1.printMetadata()

#app1.toJSONFile('aa.json')
#aa = mp.MupifObject('aa.json')
# aa.printMetadata()

app2.initialize(metadata=executionMetadata)

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
    istep = mp.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mp.U.s, number=timestepnumber)

    try:
        # solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.get(mp.DataID.PID_Time_step, app2.getAssemblyTime(istep))
        app2.set(c)
        # solve second sub-problem 
        app2.solveStep(istep)

        prop = app2.get(mp.DataID.PID_Time, app2.getAssemblyTime(istep))
        # print (istep.getTime(), c, prop)
        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f app1-time step %5.2f, app2-cummulative time %5.2f" % (
            atime.getValue(), c.getValue(atime), prop.getValue(atime)))
        
    except mp.APIError as e:
        log.error("mupif.APIError occurred:", e)
        log.error("Test FAILED")
        raise

if prop is not None and istep is not None and abs(prop.getValue(istep.getTime())-5.5) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
# c.printMetadata()
# c.validateMetadata(dataID.DataSchema)
app1.terminate()
app2.terminate()
