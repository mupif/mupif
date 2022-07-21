import Pyro5
import sys
sys.path.append('../..')
sys.path.append('..')
import models
from mupif import *
import mupif as mp
import logging

log = logging.getLogger()


class Example06(mp.Workflow):

    def __init__(self, metadata=None):
        """
        Initializes the workflow.
        """
        MD = {
            'Name': 'Thermo-mechanical stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'stationary thermo-mechanical problem using finite elements on rectangular domain',
            # 'Dependencies' are generated automatically
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Temperature', 'Name': 'Temperature field',
                 'Description': 'Temperature field on 2D domain', 'Units': 'degC'},
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}
            ],
            'Models': [
                {
                    'Name': 'thermal',
                    'Module': 'models',
                    'Class': 'ThermalModel'
                },
                {
                    'Name': 'mechanical',
                    'Module': 'models',
                    'Class': 'MechanicalModel'
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        thermalInputFile = mp.PyroFile(filename='inputT.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        # self.daemon.register(thermalInputFile)
        self.getModel('thermal').set(thermalInputFile)

        mechanicalInputFile = mp.PyroFile(filename='inputM.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        # self.daemon.register(mechanicalInputFile)
        self.getModel('mechanical').set(mechanicalInputFile)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        self.getModel('thermal').solveStep(istep, stageID, runInBackground)
        self.getModel('mechanical').set(self.getModel('thermal').get(DataID.FID_Temperature, istep.getTime()))
        self.getModel('mechanical').solveStep(istep, stageID, runInBackground)

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == DataID.FID_Temperature:
            return self.getModel('thermal').get(objectTypeID, time, objectID)
        elif objectTypeID == DataID.FID_Displacement:
            return self.getModel('mechanical').get(objectTypeID, time, objectID)
        else:
            raise apierror.APIError('Unknown field ID')

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Example06 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


md = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

demo = Example06()
demo.initialize(metadata=md)
demo.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')

tstep = timestep.TimeStep(time=1*mp.U.s, dt=1*mp.U.s, targetTime=10*mp.U.s)

demo.solveStep(tstep)

tf = demo.get(DataID.FID_Temperature, tstep.getTime())
# tf.toMeshioMesh.write('thermal10.vtk')
# tf.field2Image2D(title='Thermal', fileName='thermal.png')
# time.sleep(1)
t_val = tf.evaluate((4.1, 0.9, 0.0))

mf = demo.get(DataID.FID_Displacement, tstep.getTime())
# mf.toMeshioMesh.write('mechanical10')
# mf.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')
# time.sleep(1)
m_val = mf.evaluate((4.1, 0.9, 0.0))
print(t_val.getValue()[0], m_val.getValue()[1])

demo.printMetadata()
demo.terminate()

if ((abs(t_val.getValue()[0]-4.499411952121665) <= 1.e-8) and
        (abs(m_val.getValue()[1]-(-1.0496318531310624e-05)) <= 1.e-8)):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    print(t_val.getValue()[0], m_val.getValue()[1])
    sys.exit(1)
