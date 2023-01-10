import Pyro5
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
import mupif as mp
import logging
log = logging.getLogger()

MechanicalModel = mp.demo.MechanicalModel


@Pyro5.api.expose
class MUPIF_M_demo(mp.Model):

    def __init__(self, workDir=''):
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
                    "Units": "degC",
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
                    "Obj_ID": "max_displacement",
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
                "jobManName": "MUPIF_Mechanical_demo"
            }
        }

        super().__init__(workDir=workDir, metadata=MD)

        self.ns = None
        self.daemon = None

        self.m = None

        self.inp_field = None
        self.out_field = None
        self.w_max = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        self.ns = mp.pyroutil.connectNameserver()
        self.daemon = mp.pyroutil.getDaemon(self.ns)

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Field) and obj.getDataID() == mp.DataID.FID_Temperature:
            self.inp_field = obj

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.FID_Displacement:
            return self.out_field
        if objectTypeID == mp.DataID.PID_maxDisplacement:
            return self.w_max
        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.m = MechanicalModel()
        self.m.initialize(metadata={'Execution': self.getMetadata('Execution')})

        mechanicalInputFile = mp.PyroFile(filename='./m.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        self.daemon.register(mechanicalInputFile)
        self.m.set(mechanicalInputFile)

        self.m.set(self.inp_field)

        ts = mp.TimeStep(time=0, dt=1, targetTime=1, unit=mp.U.s, number=1)
        self.m.solveStep(ts)
        self.out_field = self.m.get(mp.DataID.FID_Displacement, time=tstep.getTargetTime())

        w_max = self.out_field.evaluate([1., 0., 0.])[1]
        self.w_max = mp.ConstantProperty(quantity=w_max, propID=mp.DataID.PID_maxDisplacement, valueType=mp.ValueType.Scalar, time=None)

    def finishStep(self, tstep):
        pass

    def getCriticalTimeStep(self):
        return 1000. * mp.U.s

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
        appName='MUPIF_Mechanical_demo',
        maxJobs=10,
        includeFiles=['m.in']
    ).runServer()
