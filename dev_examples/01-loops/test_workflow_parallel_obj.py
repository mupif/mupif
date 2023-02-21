import mupif
import Pyro5
import time
import random
import logging
log = logging.getLogger()

num_models = 3
keys = [i for i in range(1, num_models+1)]

inp_array = []
for m in keys:
    inp_array.append(mupif.ConstantProperty(value=random.randint(5, 20), propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None))

input_mupif_array = mupif.MupifObjectList(inp_array)


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
                    "Name": "m",
                    "Jobmanager": "TestModel",
                    "Instantiate": False
                }
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
        idx = 0
        for obj in input_mupif_array.objs:
            idx += 1
            mname = str(idx)
            self.inputs[mname] = obj
            self.outputs[mname] = None
            self.states[mname] = False

    def set(self, obj, objectID=""):
        pass

    def get(self, objectTypeID, time=None, objectID=''):
        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # instantiate models
        idx = 0
        for ik in self.inputs.keys():
            idx += 1
            mname = str(idx)
            self._allocateModelByName(name='m', name_new=mname)
        self._initializeAllModels()

        # execute
        for ik in self.inputs.keys():
            print(ik)
            self.getModel(ik).set(self.inputs[ik])
            self.getModel(ik).solveStep(tstep, runInBackground=True)
        all_done = False
        while not all_done:
            all_done = True
            for ik in self.inputs.keys():
                if not self.states[ik]:
                    self.states[ik] = self.getModel(ik).isSolved()
                    if self.states[ik]:
                        self.getModel(ik).finishStep(tstep)
                        self.outputs[ik] = self.getModel(ik).get(objectTypeID=mupif.DataID.ID_None)
                        # self.outputs[m] = p.inUnitsOf('').getValue()
                    else:
                        all_done = False

            strings = ['X' if self.states[mn] else '_' for mn in self.inputs.keys()]
            print(''.join(strings))
            time.sleep(1)

        print("Inputs:")
        print([self.inputs[mn].inUnitsOf('').getValue() for mn in self.inputs.keys()])
        print("Outputs:")
        print([self.outputs[mn].inUnitsOf('').getValue() for mn in self.inputs.keys()])


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
