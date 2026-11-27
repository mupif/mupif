"""
The model of example 15: cumulates the time steps it is given, like Application2 of example 02,
but computed with numpy of its own environment. It also reports the environment it runs in
(:meth:`Example15Model.getEnvironment`), so that the example can show where the execution server
ran it.
"""
import os
import sys

import numpy
import Pyro5.api
import mupif as mp


@Pyro5.api.expose
class Example15Model(mp.Model):
    contrib: mp.ConstantProperty = mp.ConstantProperty(quantity=1*mp.U.s, propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, time=0.*mp.U.s)

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Example 15 model',
            # the model ID: the ID of the package (mupif-model.toml) workflows ask for
            'ID': 'mupif-example15',
            'Description': 'Cumulates time steps (numpy), run from a model package',
            'Version_date': '1.0, Nov 2026',
            'Physics': {'Type': 'Other', 'Entity': 'Other'},
            'Solver': {
                'Software': 'Python script', 'Language': 'Python3', 'License': 'LGPL', 'Creator': 'MuPIF',
                'Version_date': '11/2026', 'Type': 'Summator', 'Documentation': 'examples/15-executionServer',
                'Estim_time_step_s': 1, 'Estim_comp_time_s': 0.01, 'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01, 'Required_expertise': 'None', 'Accuracy': 'High',
                'Sensitivity': 'High', 'Complexity': 'Low', 'Robustness': 'High'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True,
                 'Set_at': 'timestep', 'ValueType': 'Scalar'}
            ],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cumulative time',
                 'Description': 'Cumulative time', 'Units': 's', 'Origin': 'Simulated', 'ValueType': 'Scalar'}
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.steps = []

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=''):
        if obj.isInstance(mp.Property) and obj.getPropertyID() == mp.DataID.PID_Time_step:
            self.contrib = obj
        else:
            raise mp.APIError('Unknown DataID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.steps.append(self.contrib.inUnitsOf(mp.U.s).getValue(tstep.getTime()))

    def get(self, objectTypeID, time=None, objectID=''):
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=float(numpy.sum(self.steps)), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        raise mp.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 1.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return 'Example15Model'

    def getEnvironment(self):
        'Where the model runs: interpreter, environment prefix, numpy and mupif versions.'
        return {'executable': sys.executable, 'prefix': sys.prefix, 'conda_prefix': os.environ.get('CONDA_PREFIX', ''),
                'numpy': numpy.__version__, 'mupif': os.path.dirname(mp.__file__)}
