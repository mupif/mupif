#!/usr/bin/env python
import Pyro5
import threading
import time as timeT
import sys
import os
sys.path.extend(['..', '../..'])
from mupif import *
import logging
log = logging.getLogger()

start = timeT.time()
log.info('Timer started')
import mupif as mp


class Example08(mp.Workflow):
   
    def __init__(self, metadata={}):
        """
        Construct the workflow. As the workflow is non-stationary, we allocate individual 
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
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}
            ],
            'Models': [
                {
                    'Name': 'thermal',
                    'Module': '',
                    'Class': '',
                    'Jobmanager': 'thermal-nonstat-ex08'
                },
                {
                    'Name': 'mechanical',
                    'Module': '',
                    'Class': '',
                    'Jobmanager': 'mechanical-ex08'
                }
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.daemon = Pyro5.api.Daemon()
        threading.Thread(target=self.daemon.requestLoop).start()
    
    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        ival = super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        if ival is False:
            return False

        print(self._models)

        # # Connecting directly to mechanical instance, not using jobManager
        # self.mechanical = pyroutil.connectApp(ns, 'mechanical-ex08')

        thermalSignature = self.getModel('thermal').getApplicationSignature()
        log.info("Working thermal server " + thermalSignature)
        mechanicalSignature = self.getModel('mechanical').getApplicationSignature()
        log.info("Working mechanical server " + mechanicalSignature)

        # To be sure update only required passed metadata in models
        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        ival = self.getModel('thermal').initialize(
            workdir=self.getJobManager('thermal').getJobWorkDir(self.getModel('thermal').getJobID()),
            metadata=passingMD
        )
        if ival is False:
            return False
        thermalInputFile = mp.PyroFile(filename='..'+os.path.sep+'06-stacTM-local'+os.path.sep+'inputT.in', mode="rb")
        self.daemon.register(thermalInputFile)
        self.getModel('thermal').set(thermalInputFile)

        ival = self.getModel('mechanical').initialize(
            workdir='.',
            metadata=passingMD
        )
        if ival is False:
            return False
        mechanicalInputFile = mp.PyroFile(filename='..' + os.path.sep + '06-stacTM-local' + os.path.sep + 'inputM.in', mode="rb")
        self.daemon.register(mechanicalInputFile)
        self.getModel('mechanical').set(mechanicalInputFile)

        # self.getModel('thermal').printMetadata()
        # self.getModel('mechanical').printMetadata()

        return True

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving thermal problem")
        log.info(self.getModel('thermal').getApplicationSignature())
        
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        # suppress show meshio warnings that writing VTK ASCII is for debugging only
        import logging
        level0=logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)

        self.getModel('thermal').solveStep(istep)
        f = self.getModel('thermal').get(DataID.FID_Temperature, self.getModel('mechanical').getAssemblyTime(istep))
        data = f.toMeshioMesh().write('T_%02d.vtk' % istep.getNumber(), binary=True)

        self.getModel('mechanical').set(f)
        sol = self.getModel('mechanical').solveStep(istep)
        f = self.getModel('mechanical').get(DataID.FID_Displacement, istep.getTime())
        data = f.toMeshioMesh().write('M_%02d.vtk' % istep.getNumber(), binary=True)

        logging.getLogger().setLevel(level0)

    def finishStep(self, tstep):
        self.getModel('thermal').finishStep(tstep)
        self.getModel('mechanical').finishStep(tstep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min(self.getModel('thermal').getCriticalTimeStep(), self.getModel('mechanical').getCriticalTimeStep())

    def terminate(self):
        self.daemon.shutdown()
        super().terminate()
    
    def getApplicationSignature(self):
        return "Example08 workflow 1.0 - Thermo-mechanical non-stationary problem"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    demo = Example08()
    workflowMD = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    demo.initialize(metadata=workflowMD)
    demo.set(mp.ConstantProperty(value=10. * mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo.solve()
    demo.printMetadata()
    demo.terminate()
