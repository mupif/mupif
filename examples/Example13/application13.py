import sys
import os
import Pyro5
import logging
sys.path.extend(['..', '../..'])
import mupif as mp

log = logging.getLogger()


@Pyro5.api.expose
class Application13(mp.Model):
    """
    Simple application which sums given time values times 2
    """
    def __init__(self, metadata={}, **kwargs):
        MD = {
            'Name': 'Simple multiplicator',
            'ID': 'N/A',
            'Description': 'Computes multiplication of two given values',
            'Version_date': '12/2021',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Python script',
                'Language': 'Python3',
                'License': 'LGPL',
                'Creator': 'Stanislav',
                'Version_date': '12/2021',
                'Type': 'Multiplicator',
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Value_1', "Obj_ID": 1,
                 'Description': 'Input value 1', 'Units': 's', 'Required': True, "Set_at": "timestep"},
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Value_2', "Obj_ID": 2,
                 'Description': 'Input value 2', 'Units': 's', 'Required': True, "Set_at": "timestep"}
            ],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Multiplication_result',
                 'Description': 'Result of multiplication', 'Units': 's'}
            ]
        }
        super().__init__(metadata=MD, **kwargs)
        self.updateMetadata(metadata)
        self.result = 0.
        self.value_1 = 0.
        self.value_2 = 0.

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=(self.result,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)

    def set(self, obj, objectID=0):
        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mp.DataID.PID_Time:
                if objectID == 1:
                    self.value_1 = obj.inUnitsOf(mp.U.s).getValue()[0]
                if objectID == 2:
                    self.value_2 = obj.inUnitsOf(mp.U.s).getValue()[0]

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.result = self.value_1 * self.value_2

    def getCriticalTimeStep(self):
        return 1000.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application13"
