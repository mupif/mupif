import sys
import Pyro5
import logging
sys.path.extend(['..', '../..'])
import mupif as mp

log = logging.getLogger()


@Pyro5.api.expose
class Application2(mp.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Simple application cummulating time steps',
            'ID': 'N/A',
            'Description': 'Cummulates time steps',
            'Version_date': '02/2019',
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
                 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep", "ValueType": "Scalar"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated', "ValueType": "Scalar"}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.0
        self.count = 0.0
        self.contrib = mp.ConstantProperty(
            value=0., propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        # import pprint.prrint
        # pprint(self.metadata)
        # sys.exit(1)
        return super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

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
        self.value = self.value+self.contrib.inUnitsOf(mp.U.s).getValue(tstep.getTime())
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application2"
