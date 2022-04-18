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


class Example08(workflow.Workflow):
   
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
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.thermal = None
        self.mechanical = None
        self.thermalJobMan = None

        self.daemon = Pyro5.api.Daemon()
        threading.Thread(target=self.daemon.requestLoop).start()
    
    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        # locate nameserver
        ns = pyroutil.connectNameserver()
        # connect to JobManager running on (remote) server
        self.thermalJobMan = pyroutil.connectJobManager(ns, 'thermal-nonstat-ex08')
        
        try:
            self.thermal = pyroutil.allocateApplicationWithJobManager(
                ns, self.thermalJobMan
            )
            log.info('Created thermal job')
        except Exception as e:
            log.exception(e)
            log.error('HSDFSD')
            self.terminate()

        # Connecting directly to mechanical instance, not using jobManager
        self.mechanical = pyroutil.connectApp(ns, 'mechanical-ex08')

        thermalSignature = self.thermal.getApplicationSignature()
        log.info("Working thermal server " + thermalSignature)
        mechanicalSignature = self.mechanical.getApplicationSignature()
        log.info("Working mechanical server " + mechanicalSignature)

        self.registerModel(self.thermal, 'thermal_8')
        self.registerModel(self.mechanical, 'mechanical_8')

        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        # To be sure update only required passed metadata in models
        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.thermal.initialize(
            workdir=self.thermalJobMan.getJobWorkDir(self.thermal.getJobID()),
            metadata=passingMD
        )
        thermalInputFile = mp.PyroFile(filename='..'+os.path.sep+'06-stacTM-local'+os.path.sep+'inputT.in', mode="rb")
        self.daemon.register(thermalInputFile)
        self.thermal.set(thermalInputFile)

        self.mechanical.initialize(
            workdir='.',
            metadata=passingMD
        )
        mechanicalInputFile = mp.PyroFile(filename='..' + os.path.sep + '06-stacTM-local' + os.path.sep + 'inputM.in', mode="rb")
        self.daemon.register(mechanicalInputFile)
        self.mechanical.set(mechanicalInputFile)

        # self.thermal.printMetadata()
        # self.mechanical.printMetadata()

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving thermal problem")
        log.info(self.thermal.getApplicationSignature())
        
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        # suppress show meshio warnings that writing VTK ASCII is for debugging only
        import logging
        level0=logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)

        self.thermal.solveStep(istep)
        f = self.thermal.get(DataID.FID_Temperature, self.mechanical.getAssemblyTime(istep))
        data = f.toMeshioMesh().write('T_%02d.vtk' % istep.getNumber(), binary=True)

        self.mechanical.set(f)
        sol = self.mechanical.solveStep(istep) 
        f = self.mechanical.get(DataID.FID_Displacement, istep.getTime())
        data = f.toMeshioMesh().write('M_%02d.vtk' % istep.getNumber(), binary=True)

        logging.getLogger().setLevel(level0)

    def finishStep(self, tstep):
        self.thermal.finishStep(tstep)
        self.mechanical.finishStep(tstep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min(self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        self.daemon.shutdown()
        if self.thermal is not None:
            self.thermal.terminate()
        if self.thermalJobMan is not None:
            self.thermalJobMan.terminate()
        if self.mechanical is not None:
            self.mechanical.terminate()
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
