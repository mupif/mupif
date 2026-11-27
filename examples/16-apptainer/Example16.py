"""
Example 16: a workflow whose model runs in an Apptainer container on an execution server.

As example 15, the model is given only by its model ID; its package (``package/``, made by
make_package.py) names a container image. The workflow checks that the model ran in the container:
from the package mounted at /mupif/package, in the image's userland.
"""
import os
import sys
import time
sys.path.extend(['..', '../..'])
import mupif as mp

import logging
log = logging.getLogger()


class Example16(mp.Workflow):

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Example 16',
            'ID': 'Example16',
            'Description': 'A model run in an Apptainer container by an execution server',
            'Version_date': '1.0, Nov 2026',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cumulative time',
                 'Description': 'Cumulative time', 'Units': 's', 'Origin': 'Simulated', 'ValueType': 'Scalar'}
            ],
            'Models': [{'Name': 'm1', 'ModelID': 'mupif-example16'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.result = None

    def solveStep(self, istep, stageID=0, runInBackground=False):
        m1 = self.getModel('m1')
        m1.set(mp.ConstantProperty(value=1000, propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s))
        m1.solveStep(istep)
        self.result = m1.get(mp.DataID.PID_Time, istep.getTime())

    def get(self, objectTypeID, time=None, objectID=''):
        if objectTypeID == mp.DataID.PID_Time and self.result is not None:
            return mp.ConstantProperty(value=self.result.getValue(time), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        raise mp.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return 'Example16 workflow 1.0'

    def getAPIVersion(self):
        return '1.0'


def waitForServer(name='mupif/example16/exec', timeout=900.):
    'The server builds the image first (minutes, the first time): wait until it is registered.'
    ns = mp.pyroutil.connectNameserver()
    t0 = time.time()
    while name not in ns.list(prefix=name):
        if time.time() - t0 > timeout:
            raise RuntimeError(f'Execution server {name} not registered after {timeout} s')
        if int(time.time() - t0) % 30 == 0:
            log.info(f'Waiting for execution server {name} (building the image?) ...')
        time.sleep(1)


if __name__ == '__main__':
    waitForServer()
    targetTime = 1.*mp.U.s
    wf = Example16(metadata={'Execution': {'ID': '1', 'Use_case_ID': '1_1', 'Task_ID': '1'}})
    wf.initialize()
    wf.solve()
    value = wf.result.getValue(targetTime)
    env = wf.getModel('m1').getEnvironment()
    packages = wf.getModelPackages()
    wf.terminate()
    log.info(f'Model m1: package {packages.get("m1")}, environment {env}')
    ok = True
    if value != 1000.:
        log.error(f'Wrong result {value} (expected 1000)'); ok = False
    if packages.get('m1', {}).get('ID') != 'mupif-example16':
        log.error('The model did not run from the model package'); ok = False
    # in the container: the package is mounted at /mupif/package, the interpreter is the image's
    if env['file'] != '/mupif/package/ex16model/model.py' or env['python'] == sys.executable:
        log.error(f'The model did not run in the container ({env})'); ok = False
    log.info('Test OK' if ok else 'Test FAILED')
    sys.exit(0 if ok else 1)
