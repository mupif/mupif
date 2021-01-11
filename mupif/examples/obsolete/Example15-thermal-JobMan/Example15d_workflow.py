import sys
sys.path.extend(['..','../../..'])
from mupif import *
import Pyro4
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from thermalServerConfig import serverConfig
cfg = serverConfig(mode)
import logging
log = logging.getLogger()
import time as timeT
import mupif.physics.physicalquantities as PQ


class Demo15d(workflow.Workflow):
   
    def __init__ (self, targetTime=PQ.PhysicalQuantity('0 s')):
        """
        Initializes the workflow.
        """
        super(Demo15d, self).__init__(targetTime=targetTime)

    def initialize(self):
        #locate nameserver
        ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
        #connect to JobManager running on (remote) server
        self.thermalJobMan = pyroutil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
        self.thermalSolver = None

        #allocate the application instances
        try:
            self.thermalSolver = pyroutil.allocateApplicationWithJobManager( ns, self.thermalJobMan, cfg.jobNatPorts[0], cfg.hkey, pyroutil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
            log.info('Created thermal job')
 
        except Exception as e:
            log.exception(e)
        else:
            if ((self.thermalSolver is not None)):
                thermalSolverSignature=self.thermalSolver.getApplicationSignature()
                log.info("Working thermal solver on server " + thermalSolverSignature)

                log.info("Uploading input files to servers")
                pf = self.thermalJobMan.getPyroFile(self.thermalSolver.getJobID(), "input.in", 'wb')
                pyroutil.uploadPyroFile("inputT.in", pf, cfg.hkey)
            else:
                log.debug("Connection to server failed, exiting")

    def solveStep(self, istep, stageID=0, runInBackground=False):

        start = timeT.time()
        log.info('Timer started')
        log.info("Solving thermal problem")
        log.info(self.thermalSolver.getApplicationSignature())
        self.thermalSolver.solveStep(istep)
        log.info("Thermal problem solved")
        # get temperature field
        temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
        temperatureField.field2VTKData().tofile('T_distributed')
        #terminate
        log.info("Time consumed %f s" % (timeT.time()-start))


    def getCriticalTimeStep(self):
        # determine critical time step
        return PQ.PhysicalQuantity(1.0, 's')

    def terminate(self):
        #terminate solver, job manager, and super
        self.thermalSolver.terminate()
        self.thermalJobMan.terminate()
        super(Demo15d, self).terminate()

    def getApplicationSignature(self):
        return "Demo15 distributed workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo15d(targetTime=PQ.PhysicalQuantity(1.,'s'))
    demo.initialize()
    demo.solve()
    log.info("Test OK")


