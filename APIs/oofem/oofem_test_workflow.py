import mupif
import Pyro5
import logging
log = logging.getLogger()


@Pyro5.api.expose
class OOFEMTestWorkflow(mupif.Workflow):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "OOFEMTestWorkflow",
            "ModuleName": "oofem_test_workflow",
            "Name": "OOFEMTestWorkflow",
            "ID": "OOFEM_test_workflow",
            "Description": "",
            "Execution_settings": {
                "Type": "Local"
            },
            "Inputs": [
                mupif.workflow.workflow_input_targetTime_metadata,
                mupif.workflow.workflow_input_dt_metadata
            ],
            "Outputs": [
            ],
            "Models": [
                {
                    "Name": "thermal",
                    "Jobmanager": "OOFEM_API"
                },
                {
                    "Name": "mechanical",
                    "Jobmanager": "OOFEM_API"
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        ns = mupif.pyroutil.connectNameserver()
        self.daemon = mupif.pyroutil.getDaemon(ns)

        inp_file_t = mupif.PyroFile(filename='./testt.oofem.in', mode="rb", dataID=mupif.DataID.ID_InputFile)
        self.daemon.register(inp_file_t)
        self.getModel('thermal').set(inp_file_t)

        inp_file_m = mupif.PyroFile(filename='./testm.oofem.in', mode="rb", dataID=mupif.DataID.ID_InputFile)
        self.daemon.register(inp_file_m)
        self.getModel('mechanical').set(inp_file_m)

    # get method for all external outputs
    def get(self, objectTypeID, time=None, objectID=''):
        pass

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.getModel('thermal').solveStep(tstep)
        self.getModel('thermal').finishStep(tstep)

        self.getModel('mechanical').solveStep(tstep)
        self.getModel('mechanical').finishStep(tstep)


if __name__ == '__main__':
    w = OOFEMTestWorkflow()
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    w.initialize(metadata=md)

    param_targetTime = mupif.ConstantProperty(value=1., propID=mupif.DataID.PID_Time, valueType=mupif.ValueType.Scalar, unit=mupif.U.s, time=None)
    param_dt = mupif.ConstantProperty(value=0.1, propID=mupif.DataID.PID_Time, valueType=mupif.ValueType.Scalar, unit=mupif.U.s, time=None)
    w.set(param_targetTime, 'targetTime')
    w.set(param_dt, 'dt')
    w.solve()
    w.terminate()
