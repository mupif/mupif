import mupif
import Pyro5
import time
import random
import logging
log = logging.getLogger()

num_values = 30
value_keys = ["v"+str(i) for i in range(1, num_values+1)]
state_mapping = ['_', '*', 'X']

num_models = 8
model_keys = ["m"+str(i) for i in range(1, num_models+1)]


def _take_random_elem_from_list(list_val):
    n = len(list_val)
    i = random.randint(0, n-1)
    return list_val[i]


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
        self.task_state = {}
        self.model_assigned_task = {}
        self.any_unassigned_task = True
        self.any_unsolved_task = True

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        for v in value_keys:
            self.inputs[v] = random.randint(5, 20)
            self.outputs[v] = None
            self.task_state[v] = 0  # 0 = waiting, 1 = being solved, 2 = solved
        for m in model_keys:
            self.model_assigned_task[m] = None

    def set(self, obj, objectID=""):
        pass

    def get(self, objectTypeID, time=None, objectID=''):
        return None

    def _get_list_of_unassigned_tasks(self):
        res = []
        for k in value_keys:
            if self.task_state[k] == 0:
                res.append(k)
        return res

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        def _assign_task_to_model(_m, t):
            if self.model_assigned_task[_m] is None and self.task_state[t] == 0:  # just to be sure
                self.model_assigned_task[_m] = t
                self.task_state[t] = 1
                self.getModel(_m).set(mupif.ConstantProperty(value=self.inputs[t], propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None))
                self.getModel(_m).solveStep(tstep, runInBackground=True)

        def _assign_unassigned_tasks_to_unused_models():
            if self.any_unassigned_task:
                for mk in model_keys:
                    if self.any_unassigned_task:
                        if self.model_assigned_task[mk] is None:
                            free_tasks = self._get_list_of_unassigned_tasks()
                            if len(free_tasks):
                                ft = free_tasks[0]
                                ft = _take_random_elem_from_list(free_tasks)
                                _assign_task_to_model(mk, ft)
                            else:
                                self.any_unassigned_task = False
        
        def _finish_model(_m):
            self.getModel(_m).finishStep(tstep)
            p = self.getModel(_m).get(objectTypeID=mupif.DataID.ID_None)
            t = self.model_assigned_task[_m]
            self.outputs[t] = p.inUnitsOf('').getValue()
            self.task_state[t] = 2
            self.model_assigned_task[_m] = None

        def _check_models():
            for mk in model_keys:
                if self.model_assigned_task[mk] is not None:
                    if self.getModel(mk).isSolved():
                        _finish_model(mk)

        def _check_if_everything_is_solved():
            any_unsolved = False
            for vk in value_keys:
                if self.task_state[vk] < 2:
                    any_unsolved = True
                    break
            if not any_unsolved:
                self.any_unsolved_task = False

        #

        print(''.join([state_mapping[self.task_state[v]] for v in value_keys]))
        while self.any_unsolved_task:
            # print('Checking tasks and models')

            _check_models()
            _assign_unassigned_tasks_to_unused_models()
            _check_if_everything_is_solved()
            print(''.join([state_mapping[self.task_state[v]] for v in value_keys]))
            time.sleep(1)

        print("Inputs:")
        print([self.inputs[v] for v in value_keys])
        print("Outputs:")
        print([self.outputs[v] for v in value_keys])


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
