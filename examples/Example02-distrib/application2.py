import sys
import Pyro5
import logging
sys.path.extend(['..', '../..'])
import mupif as mp
#from mupif import *

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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.0
        self.count = 0.0
        self.contrib = mp.ConstantProperty(
            value=(0.,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.Q.s)

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        #import pprint.prrint
        #pprint(self.metadata)
        #sys.exit(1)
        super().initialize(file=file, workdir=workdir, metaData=metaData, validateMetaData=validateMetaData, **kwargs)

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == mp.PropertyID.PID_Time:
            return mp.ConstantProperty(
                value=(self.value,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise apierror.APIError('Unknown property ID')

    def setProperty(self, prop, objectID=0):
        if prop.getPropertyID() == mp.PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = prop
        else:
            raise apierror.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value = self.value+self.contrib.inUnitsOf(mp.U.s).getValue(tstep.getTime())[0]
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1.*mp.Q.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application2"
