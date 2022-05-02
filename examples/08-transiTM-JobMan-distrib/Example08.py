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
                    'Jobmanager': 'thermal-nonstat-ex08'
                },
                {
                    'Name': 'mechanical',
                    'Jobmanager': 'mechanical-ex08'
                }
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.daemon = Pyro5.api.Daemon()
        threading.Thread(target=self.daemon.requestLoop).start()
    
    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        log.info("Working thermal server " + self.getModel('thermal').getApplicationSignature())
        log.info("Working mechanical server " + self.getModel('mechanical').getApplicationSignature())

        thermalInputFile = mp.PyroFile(filename='..'+os.path.sep+'06-stacTM-local'+os.path.sep+'inputT.in', mode="rb")
        self.daemon.register(thermalInputFile)
        self.getModel('thermal').set(thermalInputFile)

        mechanicalInputFile = mp.PyroFile(filename='..' + os.path.sep + '06-stacTM-local' + os.path.sep + 'inputM.in', mode="rb")
        self.daemon.register(mechanicalInputFile)
        self.getModel('mechanical').set(mechanicalInputFile)

        # self.getModel('thermal').printMetadata()
        # self.getModel('mechanical').printMetadata()

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving thermal problem")
        log.info(self.getModel('thermal').getApplicationSignature())
        
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        # suppress show meshio warnings that writing VTK ASCII is for debugging only
        import logging
        level0 = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)

        self.getModel('thermal').solveStep(istep)
        f = self.getModel('thermal').get(DataID.FID_Temperature, self.getModel('mechanical').getAssemblyTime(istep))
        f.toMeshioMesh().write('T_%02d.vtk' % istep.getNumber(), binary=True)

        self.getModel('mechanical').set(f)
        self.getModel('mechanical').solveStep(istep)
        f = self.getModel('mechanical').get(DataID.FID_Displacement, istep.getTime())
        f.toMeshioMesh().write('M_%02d.vtk' % istep.getNumber(), binary=True)

        logging.getLogger().setLevel(level0)

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
