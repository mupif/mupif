import Pyro5
import subprocess
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
sys.path.append('/home/stanislav/Projects/oofem/build')
import mupif as mp
import logging
log = logging.getLogger()


@Pyro5.api.expose
class OOFEM_T_demo(mp.Model):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "OOFEM_T_demo",
            "ModuleName": "oofem_demo_thermal",
            "Name": "OOFEM demo API thermal",
            "ID": "OOFEM_Thermal_demo",
            "Description": "OOFEM thermal demo solver",
            "Version_date": "1.0.0, Jan 2023",
            "Inputs": [
                {
                    "Name": "temperature",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": "top_edge",
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                },
                {
                    "Name": "temperature",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": "bottom_edge",
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                }
            ],
            "Outputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "deg_C"
                }
            ],
            "Solver": {
                "Software": "OOFEM",
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
                "Language": "C++",
                "License": "LGPL",
                "Creator": "Borek Patzak",
                "Version_date": "1.0.0, Dec 2022",
                "Documentation": "oofem.org"
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
                "jobManName": "CVUT.Thermal_demo",
                "Class": "OOFEM_T_demo",
                "Module": "oofem_demo_thermal"
            }
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.input_temperature_top_edge = None
        self.input_temperature_bottom_edge = None
        self.output_temperature = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.FID_Temperature:
            if self.output_temperature is None:
                raise ValueError("Value not defined")
            return self.output_temperature

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == "top_edge":
            self.input_temperature_top_edge = obj
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == "bottom_edge":
            self.input_temperature_bottom_edge = obj

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        for inp in [self.input_temperature_top_edge, self.input_temperature_bottom_edge]:
            if inp is None:
                raise ValueError("A required input was not defined")

        # create input file from template
        file = open('inp_oofem_thermal.in', 'rt')
        inp_content = file.read()
        file.close()
        #
        inp_content = inp_content.replace('{top_temperature}', str(self.input_temperature_top_edge.inUnitsOf('deg_C').getValue()))
        inp_content = inp_content.replace('{bottom_temperature}', str(self.input_temperature_bottom_edge.inUnitsOf('deg_C').getValue()))
        #
        file = open('temp_oofem_thermal.in', 'wt')
        file.write(inp_content)
        file.close()

        # execute oofem
        result = subprocess.run(['/home/stanislav/Projects/oofem/build/oofem', '-f', 'temp_oofem_thermal.in'], capture_output=True, encoding='UTF-8', cwd=os.getcwd())

        # load the field from vtk
        filename = 'demot.out.m0.1.vtu'
        self.output_temperature = mp.Field.makeFromMeshioMesh(filename, unit={'Temperature': mp.U.deg_C, 'Displacement': mp.U.m}, time=0*mp.U.s)[0]

    def finishStep(self, tstep):
        pass

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getAPIVersion(self):
        return 1

    def getApplicationSignature(self):
        return "OOFEM_Thermal_demo"


if __name__ == '__main__':
    import oofem_demo_thermal

    ns = mp.pyroutil.connectNameserver()
    mp.SimpleJobManager(
        ns=ns,
        appClass=oofem_demo_thermal.OOFEM_T_demo,
        appName='CVUT.Thermal_demo',
        maxJobs=10,
        includeFiles=['inp_oofem_thermal.in']
    ).runServer()
