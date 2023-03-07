import mupif
import copy
import Pyro5
import threading
import time
import logging

log = logging.getLogger()


@Pyro5.api.expose
class DFTTestWorkflow(mupif.Workflow):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "DFTTestWorkflow",
            "ModuleName": "dft_test_workflow",
            "Name": "DFT test workflow",
            "ID": "dft_test_workflow",
            "Description": "",
            "Execution_settings": {
                "Type": "Local"
            },
            "Inputs": [
                {"Name": "prop_in", "Type": "mupif.Property", "Required": True, "description": "", "Type_ID": "mupif.DataID.ID_None", "Obj_ID": "prop_in", "Units": "", "Set_at": "timestep", "ValueType": "Scalar"},
                {"Name": "hs_in", "Type": "mupif.HeavyStruct", "Required": True, "description": "", "Type_ID": "mupif.DataID.ID_None", "Obj_ID": "hs_in", "Units": "", "Set_at": "timestep"}
            ],
            "Outputs": [
                {"Name": "hs_out", "Type": "*", "description": "", "Type_ID": "null", "Obj_ID": "hs_out", "Units": ""}
            ],
            "Models": [
                {
                    "Name": "model_1",
                    "Jobmanager": "UOI.DFT_Pre",
                    "Instantiate": True,
                },
                {
                    "Name": "model_2",
                    "Jobmanager": "UOI.DFT_Solve_Post",
                    "Instantiate": False,
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

        # initialization code of external input (prop_in)
        self.external_input_1 = None
        # It should be defined from outside using set() method.

        # initialization code of external input (hs_in)
        self.external_input_2 = None
        # It should be defined from outside using set() method.

        # __init__ code of variable_1 (Variable)
        self.variable_1 = None

        # __init__ code of variable_2 (Variable)
        self.variable_2 = None

        # __init__ code of allocate_model_at_runtime_1 (AllocateModelAtRuntime)
        self.allocate_model_at_runtime_1_model_names = []

        # __init__ code of run_in_background_1 (RunInBackground)
        self.run_in_background_1_model_names = []

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        ns = mupif.pyroutil.connectNameserver()
        self.daemon = mupif.pyroutil.getDaemon(ns)

    # set method for all external inputs
    def set(self, obj, objectID=''):

        # in case of mupif.PyroFile
        if obj.isInstance(mupif.PyroFile):
            pass

        # in case of mupif.Property
        if obj.isInstance(mupif.Property):
            pass
            if objectID == 'prop_in':
                self.external_input_1 = obj

        # in case of mupif.Field
        if obj.isInstance(mupif.Field):
            pass

        # in case of mupif.HeavyStruct
        if obj.isInstance(mupif.HeavyStruct):
            pass
            if objectID == 'hs_in':
                self.external_input_2 = obj

        # in case of mupif.String
        if obj.isInstance(mupif.String):
            pass

    # get method for all external outputs
    def get(self, objectTypeID, time=None, objectID=''):
        if objectID == 'hs_out':
            return self.variable_1

        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        pass

        # execution code of model_1 (DFT Pre)
        self.getModel('model_1').set(self.external_input_1, '')
        self.getModel('model_1').set(self.external_input_2, '')
        self.getModel('model_1').solveStep(tstep=tstep, runInBackground=False)

        # execution code of variable_1 (Variable)
        self.variable_1 = self.getModel('model_1').get(mupif.DataID.ID_None, None, 'out_hs')

        # execution code of variable_2 (Variable)
        self.variable_2 = self.getModel('model_1').get(mupif.DataID.ID_None, None, 'out_strings')

        # execution code of dowhile_1 (DoWhile)
        dowhile_1_counter = 0
        dowhile_1_compute = dowhile_1_counter < len(self.variable_2.objs)
        while dowhile_1_compute:
            dowhile_1_counter += 1

            # execution code of model_2 (DFT Solve Post)
            model_name = self.generateNewModelName(base='model_2')
            self._allocateModelByName(name='model_2', name_new=model_name)
            self.getModel(model_name).initialize(metadata=self._getInitializationMetadata())
            self.allocate_model_at_runtime_1_model_names.append(model_name)
            self.run_in_background_1_model_names.append(model_name)
            self.getModel(model_name).set(self.variable_2.objs[int(dowhile_1_counter) - 1] if 0 <= int(dowhile_1_counter) - 1 < len(self.variable_2.objs) else None, '')
            self.getModel(model_name).set(self.variable_1, '')
            self.getModel(model_name).solveStep(tstep=tstep, runInBackground=True)

            dowhile_1_compute = dowhile_1_counter < len(self.variable_2.objs)

        # execution code of wait_for_background_processes_1 (WaitForBackgroundProcesses)
        wait_for_background_processes_1_all_done = False
        while not wait_for_background_processes_1_all_done:
            time.sleep(60)
            wait_for_background_processes_1_all_done = True
            for wait_for_background_processes_1_model_name in self.run_in_background_1_model_names:
                if not self.getModel(wait_for_background_processes_1_model_name).isSolved():
                    wait_for_background_processes_1_all_done = False
            for wait_for_background_processes_1_model_name in self.run_in_background_1_model_names:
                self.getModel(wait_for_background_processes_1_model_name).finishStep(tstep)

