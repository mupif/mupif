import mupif
import Pyro5
import time
import random
import logging
log = logging.getLogger()

num_inputs = 20
input_mupif_array = mupif.MupifObjectList([mupif.ConstantProperty(value=random.randint(5, 20), propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None) for m in [i for i in range(1, num_inputs+1)]])


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
                {
                    "Name": "Input data array",
                    "Type": "mupif.MupifObjectList",
                    "Required": True,
                    "Type_ID": "mupif.DataID.ID_None",
                    "Units": "",
                    "Obj_ID": "",
                    "Set_at": "timestep"
                }
            ],
            "Outputs": [
                {
                    "Name": "Output data array",
                    "Type": "mupif.MupifObjectList",
                    "Type_ID": "mupif.DataID.ID_None",
                    "Units": "",
                    "Obj_ID": ""
                }
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
        self.input_array = None
        self.output_array = None
        self.inputs = {}
        self.outputs = {}
        self.states = {}

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=""):
        self.input_array = obj

    def get(self, objectTypeID, time=None, objectID=''):
        return self.output_array

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # prepare data
        idx = 0
        for obj in self.input_array.objs:
            idx += 1
            mname = str(idx)
            self.inputs[mname] = obj
            self.outputs[mname] = None
            self.states[mname] = False

        # instantiate models
        idx = 0
        for ik in self.inputs.keys():
            idx += 1
            mname = str(idx)
            self._allocateModelByName(name='m', name_new=mname)
        self._initializeAllModels()

        # execute
        for ik in self.inputs.keys():
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

        self.output_array = mupif.MupifObjectList([val for val in self.outputs.values()])


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
    w.set(input_mupif_array, 'input_array')
    w.solve()
    output_mupif_array = w.get(mupif.DataID.ID_None, 'input_array')
    w.terminate()

    print(input_mupif_array)
    print(output_mupif_array)

    print("Inputs:")
    print([obj.inUnitsOf('').getValue() for obj in input_mupif_array.objs])
    print("Outputs:")
    print([obj.inUnitsOf('').getValue() for obj in output_mupif_array.objs])
