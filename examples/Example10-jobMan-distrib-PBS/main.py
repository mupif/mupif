import sys
import Pyro5
sys.path.extend(['..', '../..'])
import logging
log = logging.getLogger()

from exconfig import ExConfig
import threading
cfg = ExConfig()
import mupif as mp

threading.current_thread().setName('ex10-main')


@Pyro5.api.expose
class Workflow10(mp.workflow.Workflow):

    def __init__(self, metadata={}):
        MD = {
            "ClassName": "Workflow13",
            "ModuleName": "main.py",
            "Name": "Example10 workflow",
            "ID": "workflow_10",
            "Description": "",
            "Inputs": [
                mp.workflow.workflow_input_targetTime_metadata,
                mp.workflow.workflow_input_dt_metadata
            ],
            "Outputs": [
                # duplicates outputs of the contained model
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cummulated time value',
                 'Description': 'Cummulative time', 'Units': 's'}
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

        self.ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
        self.daemon = mp.pyroutil.getDaemon(self.ns)

        # initialization code of model_1
        self.model_1_jobman = mp.pyroutil.connectJobManager(self.ns, cfg.jobManName)
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
        super().set(obj=obj, objectID=objectID)

    def terminate(self):
        self.model_1.terminate()

    def finishStep(self, tstep):
        self.model_1.finishStep(tstep)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time_property = mp.ConstantProperty(value=(tstep.getTime().inUnitsOf(mp.U.s),), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)
        self.model_1.set(obj=time_property, objectID=1)
        self.model_1.solveStep(tstep=tstep, stageID=stageID, runInBackground=runInBackground)

    def getCriticalTimeStep(self):
        return self.model_1.getCriticalTimeStep()


if __name__ == '__main__':

    # inputs
    targetTime = 2.
    dt = 1.

    # input properties
    param_targetTime = mp.ConstantProperty(value=(targetTime,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)
    param_dt = mp.ConstantProperty(value=(dt,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)

    workflow = Workflow10()

    # these metadata are supposed to be filled before execution
    md = {
        'Execution': {
            'ID': 'N/A',
            'Use_case_ID': 'N/A',
            'Task_ID': 'N/A'
        }
    }
    workflow.initialize(metadata=md)

    # set the input values defining targetTime and dt of the simulation
    workflow.set(param_targetTime, 'targetTime')
    workflow.set(param_dt, 'dt')

    workflow.solve()

    res_property = workflow.get(mp.DataID.PID_Time)
    value_result = res_property.inUnitsOf(mp.U.s).getValue()[0]

    workflow.terminate()

    print('Simulation has finished.')

    # testing part
    print(value_result)
    if value_result is not None and abs(value_result - 6.) <= 1.e-4:
        print("Test OK")
        log.info("Test OK")
    else:
        print("Test FAILED")
        log.error("Test FAILED")
