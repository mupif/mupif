"""
The model of example 16: cumulates the time steps it is given (as Application2 of example 02). It
runs in a container: :meth:`Example16Model.getEnvironment` reports the container's userland, so
that the example can show where it ran.
"""
import os
import platform
import sys

import Pyro5.api
import mupif as mp


def osRelease() -> str:
    'PRETTY_NAME of /etc/os-release: the userland the model runs in (the image\'s, not the host\'s).'
    try:
        for line in open('/etc/os-release'):
            if line.startswith('PRETTY_NAME='):
                return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return ''


@Pyro5.api.expose
class Example16Model(mp.Model):
    contrib: mp.ConstantProperty = mp.ConstantProperty(quantity=1*mp.U.s, propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, time=0.*mp.U.s)

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Example 16 model',
            # the model ID: the ID of the package (mupif-model.toml) workflows ask for
            'ID': 'mupif-example16',
            'Description': 'Cumulates time steps, run in a container image',
            'Version_date': '1.0, Nov 2026',
            'Physics': {'Type': 'Other', 'Entity': 'Other'},
            'Solver': {
                'Software': 'Python script', 'Language': 'Python3', 'License': 'LGPL', 'Creator': 'MuPIF',
                'Version_date': '11/2026', 'Type': 'Summator', 'Documentation': 'examples/16-apptainer',
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
        self.value = 0.

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=''):
        if obj.isInstance(mp.Property) and obj.getPropertyID() == mp.DataID.PID_Time_step:
            self.contrib = obj
        else:
            raise mp.APIError('Unknown DataID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.value += self.contrib.inUnitsOf(mp.U.s).getValue(tstep.getTime())

    def get(self, objectTypeID, time=None, objectID=''):
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=self.value, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        raise mp.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 1.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return 'Example16Model'

    def getEnvironment(self):
        'Where the model runs: the userland (os-release), interpreter, its own file, mupif.'
        return {'os': osRelease(), 'python': sys.executable, 'pythonVersion': platform.python_version(), 'file': __file__,
                'mupif': os.path.dirname(mp.__file__)}
