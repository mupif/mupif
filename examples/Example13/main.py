import sys
sys.path.extend(['..', '../..'])
import threading

threading.current_thread().setName('ex13-main')

import mupif as mp
import Pyro5
import logging

log = logging.getLogger()


@Pyro5.api.expose
class Workflow13(mp.workflow.Workflow):

    def __init__(self, metadata={}):
        MD = {
            "ClassName": "Workflow13",
            "ModuleName": "main.py",
            "Name": "Example13 workflow",
            "ID": "workflow_13",
            "Description": "Calculates multiplication of two given values using a simple model",
            "Inputs": [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Value_1', "Obj_ID": 1,
                 'Description': 'Input value 1', 'Units': 's', 'Required': True, "Set_at": "timestep"},
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Value_2', "Obj_ID": 2,
                 'Description': 'Input value 2', 'Units': 's', 'Required': True, "Set_at": "timestep"}
            ],
            "Outputs": [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Multiplication_result',
                 'Description': 'Result of multiplication', 'Units': 's^2'}
            ],
        }
        mp.workflow.Workflow.__init__(self, metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None
        self.ns = None
        self.model_1_jobman = None
        self.model_1 = None

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):

        self.updateMetadata(dictionary=metadata)

        execMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.ns = mp.pyroutil.connectNameserver()
        self.daemon = mp.pyroutil.getDaemon(self.ns)

        # initialization code of model_1 (Non-stationary thermal problem)
        self.model_1_jobman = mp.pyroutil.connectJobManager(self.ns, 'CVUT.demo01')
        try:
            self.model_1 = mp.pyroutil.allocateApplicationWithJobManager(ns=self.ns, jobMan=self.model_1_jobman)
            log.info(self.model_1)
        except Exception as e:
            log.exception(e)
        self.model_1.initialize(workdir='', metadata=execMD)
        self.registerModel(self.model_1, "model_1")

        mp.Workflow.initialize(self, workdir=workdir, metadata={}, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=0):
        return self.model_1.get(objectTypeID=objectTypeID, time=time, objectID=objectID)

    def set(self, obj, objectID=0):
        self.model_1.set(obj=obj, objectID=objectID)

    def terminate(self):
        self.model_1.terminate()

    def finishStep(self, tstep):
        self.model_1.finishStep(tstep)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.model_1.solveStep(tstep=tstep, stageID=stageID, runInBackground=runInBackground)

    def getCriticalTimeStep(self):
        return self.model_1.getCriticalTimeStep()


if __name__ == '__main__':
    # with no targetTime and dt specified
    # it leads to one-step simulation with default targetTime 1. s

    value_1 = 3.
    value_2 = 2.

    # inputs
    param_1 = mp.ConstantProperty(value=value_1, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)
    param_2 = mp.ConstantProperty(value=value_2, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)

    workflow = Workflow13()

    # these metadata are supposed to be filled before execution
    md = {
        'Execution': {
            'ID': 'N/A',
            'Use_case_ID': 'N/A',
            'Task_ID': 'N/A'
        }
    }
    workflow.initialize(metadata=md)

    # set the input values to the workfow which passes it to the models
    workflow.set(param_1, objectID=1)
    workflow.set(param_2, objectID=2)

    workflow.solve()
    res_property = workflow.get(mp.DataID.PID_Time, 1.*mp.U.s)
    value_result = res_property.inUnitsOf(mp.U.s*mp.U.s).getValue()
    workflow.terminate()

    print('Simulation has finished.')
    print('Calculated result of %f x %f = %f' % (value_1, value_2, value_result))

    if abs(value_result - 6.) <= 1.e-8:
        log.info("Test OK")
    else:
        log.error("Test FAILED")
        sys.exit(1)
