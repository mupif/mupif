import mupif
import Pyro5
import os
import time
import uuid


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

        self.dirname = "%s" % os.path.dirname(os.path.realpath(__file__))
        temp_dirname = "%s/temp" % self.dirname
        step_id = uuid.uuid4()
        self.inpfile = "%s/inp_%s.txt" % (temp_dirname, step_id)
        self.outfile = "%s/out_%s.txt" % (temp_dirname, step_id)

        self.jobid = None

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

        # submit the job
        self.jobid = mupif.pbs_tool.submit_job(command=" -v inpfile=\"%s\",outfile=\"%s\",script=\"%s/appexec.py\",dirname=\"%s\" %s/appexec.job -o %s/log.txt -e %s/err.txt" % (
            self.inpfile, self.outfile, self.dirname, self.dirname, self.dirname, self.dirname, self.dirname
        ))

        if not runInBackground:
            while not self.isSolved():
                time.sleep(5)
            self.finishStep(tstep)

    def isSolved(self):
        return mupif.pbs_tool.check_if_job_is_done(self.jobid)

    def finishStep(self, tstep):
        if os.path.exists(self.outfile):
            f = open(self.outfile, 'r')
            val = float(f.readline())
            f.close()
            self.output_Res = mupif.ConstantProperty(value=val, propID=mupif.DataID.ID_None, valueType=mupif.ValueType.Scalar, unit=mupif.U.none, time=None)
            if os.path.exists(self.inpfile):
                os.remove(self.inpfile)
            if os.path.exists(self.outfile):
                os.remove(self.outfile)
        else:
            raise mupif.APIError('Output file \'' + self.outfile + '\' not found.')

    def terminate(self):
        if os.path.exists(self.inpfile):
            os.remove(self.inpfile)
        if os.path.exists(self.outfile):
            os.remove(self.outfile)


if __name__ == '__main__':
    import test_model_pbs

    mupif.SimpleJobManager(
        ns=mupif.pyroutil.connectNameserver(),
        appClass=test_model_pbs.TestModel,
        appName='TestModel',
        maxJobs=10000,
        # includeFiles=['appexec.py']
    ).runServer()
