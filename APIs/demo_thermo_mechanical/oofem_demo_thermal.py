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

    def __init__(self, workDir=''):
        MD = {
            "ClassName": "OOFEM_T_demo",
            "ModuleName": "oofem_demo_thermal",
            "Name": "OOFEM demo API thermal",
            "ID": "OOFEM_Thermal_demo",
            "Description": "OOFEM thermal demo solver",
            "Version_date": "1.0.0, Jan 2023",
            "Inputs": [
                {
                    "Name": "edge temperature",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": [
                        "temperature_top",
                        "temperature_bottom"
                    ],
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                }
            ],
            "Outputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "degC"
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
                "jobManName": "OOFEM_Thermal_demo"
            }
        }

        super().__init__(workDir=workDir, metadata=MD)

        self.inp_top_temperature = None
        self.inp_bottom_temperature = None

        self.out_field = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        # self.inp_top_temperature = mupif.ConstantProperty(value=150., propID=mupif.DataID.PID_Temperature, valueType=mupif.ValueType.Scalar, unit=mupif.U.deg_C, time=None)
        # self.inp_bottom_temperature = mupif.ConstantProperty(value=-150., propID=mupif.DataID.PID_Temperature, valueType=mupif.ValueType.Scalar, unit=mupif.U.deg_C, time=None)

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == 'temperature_top':
            self.inp_top_temperature = obj
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == 'temperature_bottom':
            self.inp_bottom_temperature = obj

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.FID_Temperature:
            return self.out_field
        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        file = open('t.in', 'rt')
        inp_content = file.read()
        file.close()

        inp_content = inp_content.replace('{top_temperature}', str(self.inp_top_temperature.inUnitsOf('deg_C').getValue()))
        inp_content = inp_content.replace('{bottom_temperature}', str(self.inp_bottom_temperature.inUnitsOf('deg_C').getValue()))

        file = open('tt.in', 'wt')
        file.write(inp_content)
        file.close()

        result = subprocess.run(['/home/stanislav/Projects/oofem/build/oofem', '-f', 'tt.in'], capture_output=True, encoding='UTF-8', cwd=os.getcwd())

        # load the field from vtk
        filename = 'demot.out.m0.1.vtu'
        self.out_field = mp.Field.makeFromMeshioMesh(filename, unit={'Temperature': mp.U.deg_C, 'Displacement': mp.U.m}, time=0*mp.U.s)[0]

    def finishStep(self, tstep):
        pass

    def getCriticalTimeStep(self):
        return 1000. * mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getAPIVersion(self):
        return 1

    def getApplicationSignature(self):
        return "OOFEM_Thermal_demo"

    def getURI(self):
        return self.pyroURI


if __name__ == '__main__':
    import oofem_demo_thermal

    ns = mp.pyroutil.connectNameserver()
    mp.SimpleJobManager(
        ns=ns,
        appClass=oofem_demo_thermal.OOFEM_T_demo,
        appName='OOFEM_Thermal_demo',
        maxJobs=10,
        includeFiles=['t.in']
    ).runServer()
