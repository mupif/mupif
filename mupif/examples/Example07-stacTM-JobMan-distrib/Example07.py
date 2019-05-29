import sys
import os
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from thermalServerConfig import serverConfig
cfg = serverConfig(mode)
from mechanicalServerConfig import serverConfig
mCfg = serverConfig(mode)
import logging
log = logging.getLogger()
import time as timeT
import mupif.Physics.PhysicalQuantities as PQ


class Example07(Workflow.Workflow):
   
    def __init__(self, metaData={}):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        MD = {
            'Name': 'Thermo-mechanical non-stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'Non-stationary thermo-mechanical problem using finite elements on rectangular domain',
            # 'Model_refs_ID' are generated automatically
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.FieldID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}]
        }
        super(Example07, self).__init__(metaData=MD)
        self.updateMetadata(metaData)

        self.thermalJobMan = None
        self.mechanicalJobMan = None
        self.thermalSolver = None
        self.mechanicalSolver = None
        self.appsTunnel = None

    def initialize(self, file='', workdir='', targetTime=PQ.PhysicalQuantity('0 s'), metaData={}, validateMetaData=True, **kwargs):
        # locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
        # connect to JobManager running on (remote) server
        if mode == 1:
            self.thermalJobMan = PyroUtil.connectJobManager(
                ns,
                cfg.jobManName,
                cfg.hkey,
                PyroUtil.SSHContext(
                    userName=cfg.serverUserName,
                    sshClient=cfg.sshClient,
                    options=cfg.options,
                    sshHost=cfg.sshHost
                )
            )
            self.mechanicalJobMan = PyroUtil.connectJobManager(
                ns,
                mCfg.jobManName,
                cfg.hkey,
                PyroUtil.SSHContext(
                    userName=mCfg.serverUserName,
                    sshClient=mCfg.sshClient,
                    options=mCfg.options,
                    sshHost=mCfg.sshHost
                )
            )
        else:
            self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
            self.mechanicalJobMan = PyroUtil.connectJobManager(ns, mCfg.jobManName, cfg.hkey)

        # allocate the application instances
        try:
            self.thermalSolver = PyroUtil.allocateApplicationWithJobManager(
                ns,
                self.thermalJobMan,
                cfg.jobNatPorts[0],
                cfg.hkey,
                PyroUtil.SSHContext(
                    userName=cfg.serverUserName,
                    sshClient=cfg.sshClient,
                    options=cfg.options,
                    sshHost=cfg.sshHost
                )
            )
            log.info('Created thermal job')
            self.mechanicalSolver = PyroUtil.allocateApplicationWithJobManager(
                ns,
                self.mechanicalJobMan,
                mCfg.jobNatPorts[0],
                mCfg.hkey, PyroUtil.SSHContext(
                    userName=mCfg.serverUserName,
                    sshClient=mCfg.sshClient,
                    options=mCfg.options,
                    sshHost=mCfg.sshHost
                )
            )
            log.info('Created mechanical job')
            log.info('Creating reverse tunnel')
            
            # Create a reverse tunnel so mechanical server can access thermal server directly
            self.appsTunnel = PyroUtil.connectApplicationsViaClient(
                PyroUtil.SSHContext(
                    userName=mCfg.serverUserName,
                    sshClient=mCfg.sshClient,
                    options=mCfg.options,
                    sshHost=PyroUtil.getNSConnectionInfo(ns, mCfg.jobManName)[0]
                ),
                self.mechanicalSolver,
                self.thermalSolver
            )

        except Exception as e:
            log.exception(e)
        else:  # No exception
            self.addModelToListOfModels(self.thermalSolver)
            self.addModelToListOfModels(self.mechanicalSolver)

            super(Example07, self).initialize(file=file, workdir=workdir, targetTime=targetTime, metaData=metaData,
                                              validateMetaData=validateMetaData, **kwargs)
            if (self.thermalSolver is not None) and (self.mechanicalSolver is not None):

                thermalSolverSignature = self.thermalSolver.getApplicationSignature()
                log.info("Working thermal solver on server " + thermalSolverSignature)

                mechanicalSolverSignature = self.mechanicalSolver.getApplicationSignature()
                log.info("Working mechanical solver on server " + mechanicalSolverSignature)

                log.info("Uploading input files to servers")
                pf = self.thermalJobMan.getPyroFile(self.thermalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputT.in", pf, cfg.hkey)
                mf = self.mechanicalJobMan.getPyroFile(self.mechanicalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputM.in", mf, mCfg.hkey)

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
                    metaData=passingMD
                )
                self.mechanicalSolver.initialize(
                    file="./input.in",
                    workdir=self.mechanicalJobMan.getJobWorkDir(self.mechanicalSolver.getJobID()),
                    metaData=passingMD
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
        field = PyroUtil.getObjectFromURI(uri, cfg.hkey)
        self.mechanicalSolver.setField(field)
        log.info("Solving mechanical problem")
        self.mechanicalSolver.solveStep(istep)
        log.info("URI of mechanical problem's field is " +
                 str(self.mechanicalSolver.getFieldURI(FieldID.FID_Displacement, istep.getTargetTime())))
        displacementField = self.mechanicalSolver.getField(FieldID.FID_Displacement, istep.getTime())

        # save results as vtk
        temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
        temperatureField.field2VTKData().tofile('temperatureField')
        displacementField.field2VTKData().tofile('displacementField')
        log.info("Time consumed %f s" % (timeT.time()-start))

    def getCriticalTimeStep(self):
        # determine critical time step
        return PQ.PhysicalQuantity(1.0, 's')

    def terminate(self):
        self.thermalSolver.terminate()
        self.mechanicalSolver.terminate()
        self.appsTunnel.terminate()
        super(Example07, self).terminate()

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
    demo.initialize(targetTime=PQ.PhysicalQuantity(1., 's'), metaData=md)
    demo.solve()
    demo.printMetadata()
    demo.terminate()
    log.info("Test OK")
