import mupif
import Pyro5
import time
import random
import logging
log = logging.getLogger()

num_models = 20
model_keys = ["m"+str(i) for i in range(1, num_models+1)]


@Pyro5.api.expose
class LoopsTestWorkflow(mupif.Workflow):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "LoopsTestWorkflow",
            "ModuleName": "test_workflow",
            "Name": "LoopsTestWorkflow",
            "ID": "Loops_test_workflow",
            "Description": "",
            "Execution_settings": {
                "Type": "Local"
            },
            "Inputs": [
            ],
            "Outputs": [
            ],
            "Models": [
                {
                    "Name": m,
                    "Jobmanager": "TestModel"
                } for m in model_keys
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None
        self.inputs = {}
        self.outputs = {}
        self.states = {}

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        for m in model_keys:
            self.inputs[m] = random.randint(5, 20)
            self.outputs[m] = None
            self.states[m] = False

    def set(self, obj, objectID=""):
        pass

    def get(self, objectTypeID, time=None, objectID=''):
        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        for m in model_keys:
            self.getModel(m).set(mupif.ConstantProperty(value=self.inputs[m], propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None))
            self.getModel(m).solveStep(tstep, runInBackground=True)
        all_done = False
        while not all_done:
            # print('Checking isSolved()')
            all_done = True
            for m in model_keys:
                if not self.states[m]:
                    self.states[m] = self.getModel(m).isSolved()
                    if self.states[m]:
                        self.getModel(m).finishStep(tstep)
                        p = self.getModel(m).get(objectTypeID=mupif.DataID.ID_None)
                        self.outputs[m] = p.inUnitsOf('').getValue()
                    else:
                        all_done = False

            strings = ['X' if self.states[m] else '_' for m in model_keys]
            print(''.join(strings))
            time.sleep(1)

        print("Inputs:")
        print([self.inputs[m] for m in model_keys])
        print("Outputs:")
        print([self.outputs[m] for m in model_keys])


if __name__ == '__main__':
    w = LoopsTestWorkflow()
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    w.initialize(metadata=md)
    w.solve()
    w.terminate()
