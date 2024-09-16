import Pyro5
import threading
import time as timeT
import sys
sys.path.extend(['.', '..', '../..'])
from mupif import *
import mupif as mp
import logging
log = logging.getLogger()


class Example07(mp.Workflow):
   
    def __init__(self, metadata=None):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        MD = {
            'Name': 'Thermo-mechanical non-stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'Non-stationary thermo-mechanical problem using finite elements on rectangular domain',
            # 'Dependencies' are generated automatically
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm', 'ValueType': 'Vector'}
            ],
            'Models': [
                {
                    'Name': 'thermal',
                    'Jobmanager': 'Mupif.JobManager@ThermalSolver-ex07'
                },
                {
                    'Name': 'mechanical',
                    'Jobmanager': 'Mupif.JobManager@MechanicalSolver-ex07'
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        # locate nameserver
        ns = pyroutil.connectNameserver()
        self.daemon = pyroutil.getDaemon(ns)

        log.info("Working thermal solver on server " + self.getModel('thermal').getApplicationSignature())
        log.info("Working mechanical solver on server " + self.getModel('mechanical').getApplicationSignature())

        thermalInputFile = mp.PyroFile(filename='./inputT.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        self.daemon.register(thermalInputFile)
        self.getModel('thermal').set(thermalInputFile)

        mechanicalInputFile = mp.PyroFile(filename='./inputM.in', mode="rb", dataID=mp.DataID.ID_InputFile)
        self.daemon.register(mechanicalInputFile)
        self.getModel('mechanical').set(mechanicalInputFile)

    def solveStep(self, istep, stageID=0, runInBackground=False):

        start = timeT.time()
        log.info('Timer started')
        log.info("Solving thermal problem")
        log.info(self.getModel('thermal').getApplicationSignature())
        
        self.getModel('thermal').solveStep(istep)
        log.info("Thermal problem solved")
        uri = self.getModel('thermal').getFieldURI(DataID.FID_Temperature, self.getModel('mechanical').getAssemblyTime(istep))
        log.info("URI of thermal problem's field is " + str(uri))
        field = pyroutil.getObjectFromURI(uri)
        self.getModel('mechanical').set(field)
        log.info("Solving mechanical problem")
        self.getModel('mechanical').solveStep(istep)
        log.info("URI of mechanical problem's field is " + str(self.getModel('mechanical').getFieldURI(DataID.FID_Displacement, istep.getTargetTime())))
        displacementField = self.getModel('mechanical').get(DataID.FID_Displacement, istep.getTime())

        # save results as vtk
        temperatureField = self.getModel('thermal').get(DataID.FID_Temperature, istep.getTime())
        temperatureField.toMeshioMesh().write('temperatureField.vtk')
        displacementField.toMeshioMesh().write('displacementField.vtk')
        log.info("Time consumed %f s" % (timeT.time()-start))

    def getCriticalTimeStep(self):
        # determine critical time step
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Example07 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__ == '__main__':
    demo = Example07()
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    demo.initialize(metadata=md)
    demo.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo.solve()
    demo.printMetadata()
    demo.printListOfModels()
    demo.terminate()
    log.info("Test OK")
    print("OK")
