import sys
sys.path.append('../..')
sys.path.append('..')
import models
from mupif import *
import mupif as mp
import mupif.physics.physicalquantities as PQ
import time
import logging

log = logging.getLogger()


class Example06(workflow.Workflow):

    def __init__(self, metadata={}):
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
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.FieldID.FID_Temperature', 'Name': 'Temperature field',
                 'Description': 'Temperature field on 2D domain', 'Units': 'degC'},
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.FieldID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}
            ]
        }
        super(Example06, self).__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.thermalSolver = models.ThermalModel()
        self.mechanicalSolver = models.MechanicalModel()

        self.registerModel(self.thermalSolver, 'thermal')
        self.registerModel(self.mechanicalSolver, 'mechanical')

    def initialize(self, file='', workdir='', targetTime=0*mp.Q.s, metadata={}, validateMetaData=True):
        super().initialize(file=file, workdir=workdir, targetTime=targetTime, metadata=metadata,
                                          validateMetaData=validateMetaData)

        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.thermalSolver.initialize('inputT10.in', '.', metadata=passingMD)
        self.mechanicalSolver.initialize('inputM10.in', '.', metadata=passingMD)
        #self.mechanicalSolver.printMetadata(nonEmpty=False)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        self.thermalSolver.solveStep(istep, stageID, runInBackground)
        self.mechanicalSolver.setField(self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime()))
        self.mechanicalSolver.solveStep(istep, stageID, runInBackground)

    def getField(self, fieldID, time, objectID=0):
        if fieldID == FieldID.FID_Temperature:
            return self.thermalSolver.getField(fieldID, time, objectID)
        elif fieldID == FieldID.FID_Displacement:
            return self.mechanicalSolver.getField(fieldID, time, objectID)
        else:
            raise apierror.APIError('Unknown field ID')

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')

    def terminate(self):
        self.thermalSolver.terminate()
        self.mechanicalSolver.terminate()
        super(Example06, self).terminate()

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
demo.initialize(targetTime=1*mp.Q.s, metadata=md)

tstep = timestep.TimeStep(time=1*mp.Q.s,dt=1*mp.Q.s,targetTime=10*mp.Q.s)

demo.solveStep(tstep)

tf = demo.getField(FieldID.FID_Temperature, tstep.getTime())
# tf.toMeshioMesh.write('thermal10.vtk')
# tf.field2Image2D(title='Thermal', fileName='thermal.png')
# time.sleep(1)
t_val = tf.evaluate((4.1, 0.9, 0.0))

mf = demo.getField(FieldID.FID_Displacement, tstep.getTime())
# mf.toMeshioMesh.write('mechanical10')
# mf.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')
# time.sleep(1)
m_val = mf.evaluate((4.1, 0.9, 0.0))
print(t_val.getValue()[0], m_val.getValue()[1])

demo.printMetadata()
demo.terminate()

if ((abs(t_val.getValue()[0]-4.4994119521216644) <= 1.e-8) and
        (abs(m_val.getValue()[1]-(-4.170695218292803e-06)) <= 1.e-8)):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    print(t_val.getValue()[0], m_val.getValue()[1])
    sys.exit(1)
