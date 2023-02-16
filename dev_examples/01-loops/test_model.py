import mupif
import Pyro5
import subprocess
import os
import time
import logging
log = logging.getLogger()


@Pyro5.api.expose
class TestModel(mupif.Model):
    def __init__(self, metadata=None):

        MD = {
            "ClassName": "TestModel",
            "ModuleName": "test_model",
            "Name": "Test Model",
            "ID": "test_model",
            "Description": "Test model",
            "Version_date": "1.0.0, Jan 2023",
            "Inputs": [
                {
                    "Name": "Inp",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.ID_None",
                    "Units": "",
                    "Obj_ID": "",
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                }
            ],
            "Outputs": [
                {
                    "Name": "Res",
                    "Type": "mupif.Property",
                    "Type_ID": "mupif.DataID.ID_None",
                    "Units": "",
                    "Obj_ID": "",
                    "ValueType": "Scalar"
                }
            ],
            "Solver": {
                "Software": "Own",
                "Type": "tester",
                "Accuracy": "High",
                "Sensitivity": "Low",
                "Complexity": "High",
                "Robustness": "High",
                "Estim_time_step_s": 1,
                "Estim_comp_time_s": 1,
                "Estim_execution_cost_EUR": 0.01,
                "Estim_personnel_cost_EUR": 0.01,
                "Required_expertise": "None",
                "Language": "Python",
                "License": "LGPL",
                "Creator": "Stanislav Sulc",
                "Version_date": "1.0.0, Jan 2023",
                "Documentation": "not available"
            },
            "Physics": {
                "Type": "Other",
                "Entity": "Other"
            },
            "Execution_settings": {
                "Type": "Distributed",
                "jobManName": "TestModel",
                "Class": "TestModel",
                "Module": "test_model"
            }
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.d = os.getcwd()
        self.p = None

        self.inpfile = "%s/inp.txt" % self.d
        self.outfile = "%s/out.txt" % self.d

        self.input_Inp = None
        self.output_Res = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mupif.DataID.ID_None and objectID == "":
            if self.output_Res is None:
                raise ValueError("Value not defined")
            return self.output_Res

    def set(self, obj, objectID=""):
        if obj.isInstance(mupif.Property) and obj.getDataID() == mupif.DataID.ID_None and objectID == "":
            self.input_Inp = obj

    def getApplicationSignature(self):
        return "TestModel"

    def getAPIVersion(self):
        return 1

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        for inp in [self.input_Inp]:
            if inp is None:
                raise ValueError("A required input was not defined")

        file = open(self.inpfile, 'w')
        file.write(str(self.input_Inp.inUnitsOf('').getValue()))
        file.close()

        self.p = subprocess.Popen([str(os.path.dirname(os.path.abspath(__file__))) + '/appexec.py', self.inpfile, self.outfile], cwd=os.getcwd())

        if not runInBackground:
            while not self.isSolved():
                time.sleep(5)
            self.finishStep(tstep)

    def isSolved(self):
        return self.p.poll() is not None

    def finishStep(self, tstep):
        if os.path.exists(self.outfile):
            f = open(self.outfile, 'r')
            val = float(f.readline())
            f.close()
            self.output_Res = mupif.ConstantProperty(value=val, propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None)
        else:
            raise mupif.APIError('Output file \'' + self.outfile + '\' not found.')


if __name__ == '__main__':
    import test_model

    mupif.SimpleJobManager(
        ns=mupif.pyroutil.connectNameserver(),
        appClass=test_model.TestModel,
        appName='TestModel',
        maxJobs=100,
        # includeFiles=['appexec.py']
    ).runServer()
