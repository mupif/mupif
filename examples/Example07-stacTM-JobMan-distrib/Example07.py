import sys
import os
sys.path.extend(['.','..', '../..'])
from mupif import *
import mupif as mp
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from thermalServerConfig import serverConfig
cfg = serverConfig(mode)
from mechanicalServerConfig import serverConfig
mCfg = serverConfig(mode)
import logging
log = logging.getLogger()
import time as timeT
import mupif.physics.physicalquantities as PQ


class Example07(workflow.Workflow):
   
    def __init__(self, metadata={}):
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
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.FieldID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.thermalJobMan = None
        self.mechanicalJobMan = None
        self.thermalSolver = None
        self.mechanicalSolver = None
        self.appsTunnel = None

    def initialize(self, file='', workdir='', targetTime=0*mp.Q.s, metadata={}, validateMetaData=True):
        # locate nameserver
        ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
        # connect to JobManager running on (remote) server
        if mode == 1:
            sshContext=pyroutil.SSHContext(
                userName=cfg.serverUserName,
                sshClient=cfg.sshClient,
                options=cfg.options,
                sshHost=cfg.sshHost
            )
        else: sshContext=None
        self.thermalJobMan = pyroutil.connectJobManager(ns, cfg.jobManName+'-ex07', sshContext=sshContext)
        self.mechanicalJobMan = pyroutil.connectJobManager(ns, mCfg.jobManName+'-ex07', sshContext=sshContext)

        # allocate the application instances
        try:
            self.thermalSolver = pyroutil.allocateApplicationWithJobManager(
                ns,
                self.thermalJobMan,
                cfg.jobNatPorts[0],
                pyroutil.SSHContext(
                    userName=cfg.serverUserName,
                    sshClient=cfg.sshClient,
                    options=cfg.options,
                    sshHost=cfg.sshHost
                )
            )
            log.info('Created thermal job')
            self.mechanicalSolver = pyroutil.allocateApplicationWithJobManager(
                ns,
                self.mechanicalJobMan,
                mCfg.jobNatPorts[0],
                pyroutil.SSHContext(
                    userName=mCfg.serverUserName,
                    sshClient=mCfg.sshClient,
                    options=mCfg.options,
                    sshHost=mCfg.sshHost
                )
            )
            log.info('Created mechanical job')
            log.info('Creating reverse tunnel')
            
            # Create a reverse tunnel so mechanical server can access thermal server directly
            self.appsTunnel = pyroutil.connectApplicationsViaClient(
                pyroutil.SSHContext(
                    userName=mCfg.serverUserName,
                    sshClient=mCfg.sshClient,
                    options=mCfg.options,
                    sshHost=pyroutil.getNSConnectionInfo(ns, mCfg.jobManName+'-ex07')[0]
                ),
                self.mechanicalSolver,
                self.thermalSolver
            )

        except Exception as e:
            log.exception(e)
        else:  # No exception
            self.registerModel(self.thermalSolver, 'thermal')
            self.registerModel(self.mechanicalSolver, 'mechanical')

            super().initialize(file=file, workdir=workdir, targetTime=targetTime, metadata=metadata,
                                              validateMetaData=validateMetaData)
            if (self.thermalSolver is not None) and (self.mechanicalSolver is not None):

                thermalSolverSignature = self.thermalSolver.getApplicationSignature()
                log.info("Working thermal solver on server " + thermalSolverSignature)

                mechanicalSolverSignature = self.mechanicalSolver.getApplicationSignature()
                log.info("Working mechanical solver on server " + mechanicalSolverSignature)

                log.info("Uploading input files to servers")
                pf = self.thermalJobMan.getPyroFile(self.thermalSolver.getJobID(), "input.in", 'wb')
                pyroutil.uploadPyroFile("inputT.in", pf)
                mf = self.mechanicalJobMan.getPyroFile(self.mechanicalSolver.getJobID(), "input.in", 'wb')
                pyroutil.uploadPyroFile("inputM.in", mf)

                # To be sure update only required passed metadata in models
                passingMD = {
                    'Execution': {
                        'ID': self.getMetadata('Execution.ID'),
                        'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                        'Task_ID': self.getMetadata('Execution.Task_ID')
                    }
                }

                self.thermalSolver.updateMetadata(passingMD)
                self.mechanicalSolver.updateMetadata(passingMD)
                self.thermalSolver.initialize(
                    file="./input.in",
                    workdir=self.thermalJobMan.getJobWorkDir(self.thermalSolver.getJobID()),
                    metadata=passingMD
                )
                self.mechanicalSolver.initialize(
                    file="./input.in",
                    workdir=self.mechanicalJobMan.getJobWorkDir(self.mechanicalSolver.getJobID()),
                    metadata=passingMD
                )

            else:
                log.debug("Connection to server failed, exiting")

    def solveStep(self, istep, stageID=0, runInBackground=False):

        start = timeT.time()
        log.info('Timer started')
        log.info("Solving thermal problem")
        log.info(self.thermalSolver.getApplicationSignature())
        
        self.thermalSolver.solveStep(istep)
        log.info("Thermal problem solved")
        uri = self.thermalSolver.getFieldURI(FieldID.FID_Temperature, self.mechanicalSolver.getAssemblyTime(istep))
        log.info("URI of thermal problem's field is " + str(uri))
        field = pyroutil.getObjectFromURI(uri)
        self.mechanicalSolver.setField(field)
        log.info("Solving mechanical problem")
        self.mechanicalSolver.solveStep(istep)
        log.info("URI of mechanical problem's field is " +
                 str(self.mechanicalSolver.getFieldURI(FieldID.FID_Displacement, istep.getTargetTime())))
        displacementField = self.mechanicalSolver.getField(FieldID.FID_Displacement, istep.getTime())

        # save results as vtk
        temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
        temperatureField.toMeshioMesh().write('temperatureField.vtk')
        displacementField.toMeshioMesh().write('displacementField.vtk')
        log.info("Time consumed %f s" % (timeT.time()-start))

    def getCriticalTimeStep(self):
        # determine critical time step
        return 1*mp.Q.s

    def terminate(self):
        self.thermalSolver.terminate()
        self.mechanicalSolver.terminate()
        self.appsTunnel.terminate()
        super().terminate()

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
    demo.initialize(targetTime=1*mp.Q.s, metadata=md)
    demo.solve()
    demo.printMetadata()
    demo.printListOfModels()
    demo.terminate()
    log.info("Test OK")
