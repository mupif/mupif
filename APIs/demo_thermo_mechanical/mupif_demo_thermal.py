import Pyro5
import sys
import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
import mupif as mp
import logging
log = logging.getLogger()


@Pyro5.api.expose
class MUPIF_T_demo(mp.Model):
    def __init__(self, metadata=None):

        MD = {
            "ClassName": "MUPIF_T_demo",
            "ModuleName": "mupif_demo_thermal",
            "Name": "MUPIF demo API thermal",
            "ID": "MUPIF_Thermal_demo",
            "Description": "MUPIF thermal demo solver",
            "Version_date": "1.0.0, Jan 2023",
            "Inputs": [
                {
                    "Name": "temperature_top",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": "top_edge",
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                },
                {
                    "Name": "temperature_bottom",
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
                },
                {
                    "Name": "temperatureVTK",
                    "Type_ID": "mupif.DataID.ID_VTKFile",
                    "Type": "mupif.PyroFile",
                    "Units": ""
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
                "jobManName": "CVUT.Thermal_demo",
                "Class": "MUPIF_T_demo",
                "Module": "mupif_demo_thermal"
            }
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.input_temperature_top_top_edge = None
        self.input_temperature_bottom_bottom_edge = None
        self.output_temperature = None
        self.output_temperatureVTK = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.FID_Temperature:
            if self.output_temperature is None:
                raise ValueError("Value not defined")
            return self.output_temperature
        if objectTypeID == mp.DataID.ID_VTKFile:
            if self.output_temperatureVTK is None:
                raise ValueError("Value not defined")
            return self.output_temperatureVTK

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == "top_edge":
            self.input_temperature_top_top_edge = obj
        if obj.isInstance(mp.Property) and obj.getDataID() == mp.DataID.PID_Temperature and objectID == "bottom_edge":
            self.input_temperature_bottom_bottom_edge = obj

    def getApplicationSignature(self):
        return "MUPIF_T_demo"

    def getAPIVersion(self):
        return 1

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        for inp in [self.input_temperature_top_top_edge, self.input_temperature_bottom_bottom_edge]:
            if inp is None:
                raise ValueError("A required input was not defined")
        # create input file from template
        file = open('inp_mupif_thermal.in', 'rt')
        inp_content = file.read()
        file.close()
        #
        inp_content = inp_content.replace('{top_temperature}', str(self.input_temperature_top_top_edge.inUnitsOf('deg_C').getValue()))
        inp_content = inp_content.replace('{bottom_temperature}', str(self.input_temperature_bottom_bottom_edge.inUnitsOf('deg_C').getValue()))
        #
        file = open('temp_mupif_thermal.in', 'wt')
        file.write(inp_content)
        file.close()

        # execute mupif thermal model
        model = mp.demo.ThermalModel()
        model.initialize(metadata={'Execution': self.getMetadata('Execution')})
        input_file = mp.PyroFile(filename='./temp_mupif_thermal.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        model.set(input_file)
        ts = mp.TimeStep(time=0, dt=1, targetTime=1, unit=mp.U.s, number=1)
        model.solveStep(ts)
        self.output_temperature = model.get(mp.DataID.FID_Temperature, time=tstep.getTargetTime())
        self.output_temperatureVTK = model.get(mp.DataID.ID_VTKFile, time=tstep.getTargetTime())



if __name__ == '__main__':
    import mupif_demo_thermal

    ns = mp.pyroutil.connectNameserver()
    jobMan = mp.SimpleJobManager(
        ns=ns,
        appClass=mupif_demo_thermal.MUPIF_T_demo,
        appName='CVUT.Thermal_demo',
        maxJobs=10,
        includeFiles=['inp_mupif_thermal.in']
    ).runServer()
