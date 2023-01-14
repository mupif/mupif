import Pyro5
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
import mupif as mp
import logging
log = logging.getLogger()


@Pyro5.api.expose
class MUPIF_M_demo(mp.Model):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "MUPIF_M_demo",
            "ModuleName": "mupif_demo_mechanical",
            "Name": "MUPIF demo API mechanical",
            "ID": "MUPIF_Mechanical_demo",
            "Description": "MUPIF mechanical demo solver",
            "Version_date": "1.0.0, Jan 2023",
            "Inputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "deg_C",
                    "Required": True,
                    "Set_at": "timestep"
                }
            ],
            "Outputs": [
                {
                    "Name": "displacement",
                    "Type_ID": "mupif.DataID.FID_Displacement",
                    "Type": "mupif.Field",
                    "Units": "m"
                },
                {
                    "Name": "max vertical displacement",
                    "Type": "mupif.Property",
                    "Type_ID": "mupif.DataID.PID_maxDisplacement",
                    "Units": "m",
                    "Obj_ID": "",
                    "ValueType": "Scalar"
                }
            ],
            "Solver": {
                "Software": "MUPIF",
                "Type": "Finite elements",
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
                "Creator": "Borek Patzak",
                "Version_date": "1.0.0, Jan 2023",
                "Documentation": "mupif.org"
            },
            "Physics": {
                "Type": "Continuum",
                "Entity": "Other",
                "Equation": [],
                "Equation_quantities": [],
                "Relation_description": [],
                "Relation_formulation": [],
                "Representation": "Finite elements"
            },
            "Execution_settings": {
                "Type": "Distributed",
                "jobManName": "CVUT.Mechanical_demo",
                "Class": "MUPIF_M_demo",
                "Module": "mupif_demo_mechanical"
            }
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.input_temperature = None
        self.output_displacement = None
        self.output_max_vertical_displacement = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.FID_Displacement:
            if self.output_displacement is None:
                raise ValueError("Value not defined")
            return self.output_displacement
        if objectTypeID == mp.DataID.PID_maxDisplacement and objectID == "":
            if self.output_max_vertical_displacement is None:
                raise ValueError("Value not defined")
            return self.output_max_vertical_displacement

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Field) and obj.getDataID() == mp.DataID.FID_Temperature:
            self.input_temperature = obj

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        for inp in [self.input_temperature]:
            if inp is None:
                raise ValueError("A required input was not defined")

        # execute mupif mechanical model
        model = mp.demo.MechanicalModel()
        model.initialize(metadata={'Execution': self.getMetadata('Execution')})
        input_file = mp.PyroFile(filename='./inp_mupif_mechanical.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        daemon = mp.pyroutil.getDaemon(mp.pyroutil.connectNameserver())
        daemon.register(input_file)
        model.set(input_file)
        model.set(self.input_temperature)
        ts = mp.TimeStep(time=0, dt=1, targetTime=1, unit=mp.U.s, number=1)
        model.solveStep(ts)
        self.output_displacement = model.get(mp.DataID.FID_Displacement, time=tstep.getTargetTime())
        w_max = self.output_displacement.evaluate([1., 0., 0.])[1]
        self.output_max_vertical_displacement = mp.ConstantProperty(quantity=w_max, propID=mp.DataID.PID_maxDisplacement, valueType=mp.ValueType.Scalar, time=None)

    def finishStep(self, tstep):
        pass

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getAPIVersion(self):
        return 1

    def getApplicationSignature(self):
        return "MUPIF_Mechanical_demo"

    def getURI(self):
        return self.pyroURI


if __name__ == '__main__':
    import mupif_demo_mechanical

    ns = mp.pyroutil.connectNameserver()
    mp.SimpleJobManager(
        ns=ns,
        appClass=mupif_demo_mechanical.MUPIF_M_demo,
        appName='CVUT.Mechanical_demo',
        maxJobs=10,
        includeFiles=['inp_mupif_mechanical.in']
    ).runServer()
