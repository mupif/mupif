"""
Example 15: a workflow whose model is given only by its model ID; an execution server runs it.

No model server of the model runs anywhere: the execution server (``server.py``) gets the model
package ``mupif-example15`` from its registry, installs its pixi environment (on the first run) and
runs the model there. The workflow then reports which package ran (ID, version, digest) and where.
"""
import os
import sys
sys.path.extend(['..', '../..'])
import mupif as mp

import logging
log = logging.getLogger()


class Example15(mp.Workflow):

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Example 15',
            'ID': 'Example15',
            'Description': 'A model run by an execution server from a model package',
            'Version_date': '1.0, Nov 2026',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cumulative time',
                 'Description': 'Cumulative time', 'Units': 's', 'Origin': 'Simulated', 'ValueType': 'Scalar'}
            ],
            # only the model ID (and version): any execution server can run it
            'Models': [{'Name': 'm1', 'ModelID': 'mupif-example15', 'ModelVersion': '1.0'}]
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
        'The output (read by the mupifDB execution script after solve()).'
        if objectTypeID == mp.DataID.PID_Time and self.result is not None:
            return mp.ConstantProperty(value=self.result.getValue(time), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        raise mp.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return 'Example15 workflow 1.0'

    def getAPIVersion(self):
        return '1.0'


if __name__ == '__main__':
    targetTime = 1.*mp.U.s
    wf = Example15(metadata={'Execution': {'ID': '1', 'Use_case_ID': '1_1', 'Task_ID': '1'}})
    wf.initialize()
    wf.set(mp.ConstantProperty(value=targetTime, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    wf.solve()
    value = wf.result.getValue(targetTime)
    env = wf.getModel('m1').getEnvironment()
    packages = wf.getModelPackages()
    servers = wf.getModelServers()
    wf.terminate()
    log.info(f'Model m1 ran on {servers["m1"]}, package {packages.get("m1")}')
    log.info(f'Model environment: {env}')
    ok = True
    if value != 1000.:
        log.error(f'Wrong result {value} (expected 1000)'); ok = False
    if packages.get('m1', {}).get('ID') != 'mupif-example15':
        log.error('The model did not run from the model package'); ok = False
    # the model ran in the pixi environment of its package, not in the interpreter of this workflow
    if os.path.realpath(env['prefix']) == os.path.realpath(sys.prefix) or '.pixi' not in env['prefix']:
        log.error(f'The model did not run in the environment of its package ({env["prefix"]})'); ok = False
    log.info('Test OK' if ok else 'Test FAILED')
    sys.exit(0 if ok else 1)
