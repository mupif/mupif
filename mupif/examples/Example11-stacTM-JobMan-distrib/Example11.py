import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import Pyro4
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from thermalServerConfig import serverConfig
cfg = serverConfig(mode)
from mechanicalServerConfig import serverConfig
mCfg = serverConfig(mode)
import logging
log = logging.getLogger()
import time as timeT
import mupif.Physics.PhysicalQuantities as PQ


class Demo11(Workflow.Workflow):
   
    def __init__ (self, targetTime=PQ.PhysicalQuantity('0 s')):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        super(Demo11, self).__init__(targetTime=targetTime)

    def initialize(self):
        #locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
        #connect to JobManager running on (remote) server
        if(mode == 1):
            self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey, PyroUtil.SSHContext(userName = cfg.serverUserName,sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
            self.mechanicalJobMan = PyroUtil.connectJobManager(ns,mCfg.jobManName, cfg.hkey,PyroUtil.SSHContext(userName = mCfg.serverUserName, sshClient=mCfg.sshClient, options=mCfg.options, sshHost=mCfg.sshHost) )
        else:
            self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
            self.mechanicalJobMan = PyroUtil.connectJobManager(ns, mCfg.jobManName, cfg.hkey)

        self.thermalSolver = None
        self.mechanicalSolver = None

        #allocate the application instances
        try:
            self.thermalSolver = PyroUtil.allocateApplicationWithJobManager( ns, self.thermalJobMan, cfg.jobNatPorts[0], cfg.hkey, PyroUtil.SSHContext(userName = cfg.serverUserName,sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
            log.info('Created thermal job')
            self.mechanicalSolver = PyroUtil.allocateApplicationWithJobManager( ns, self.mechanicalJobMan, mCfg.jobNatPorts[0], mCfg.hkey, PyroUtil.SSHContext(userName = mCfg.serverUserName,sshClient=mCfg.sshClient, options=mCfg.options, sshHost=mCfg.sshHost ))
            log.info('Created mechanical job')
            log.info('Creating reverse tunnel')
            
            #Create a reverse tunnel so mechanical server can access thermal server directly
            self.appsTunnel = PyroUtil.connectApplicationsViaClient(PyroUtil.SSHContext(userName = mCfg.serverUserName, sshClient=mCfg.sshClient, options=mCfg.options, sshHost=PyroUtil.getNSConnectionInfo(ns, mCfg.jobManName)[0]), self.mechanicalSolver, self.thermalSolver)
        except Exception as e:
            log.exception(e)
        else:#No exception
            if ((self.thermalSolver is not None) and (self.mechanicalSolver is not None)):
                thermalSolverSignature=self.thermalSolver.getApplicationSignature()
                log.info("Working thermal solver on server " + thermalSolverSignature)

                mechanicalSolverSignature=self.mechanicalSolver.getApplicationSignature()
                log.info("Working mechanical solver on server " + mechanicalSolverSignature)

                log.info("Uploading input files to servers")
                pf = self.thermalJobMan.getPyroFile(self.thermalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputT.in", pf, cfg.hkey)
                mf = self.mechanicalJobMan.getPyroFile(self.mechanicalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputM.in", mf, mCfg.hkey)
            else:
                log.debug("Connection to server failed, exiting")

    def solveStep(self, istep, stageID=0, runInBackground=False):

        start = timeT.time()
        log.info('Timer started')
        log.info("Solving thermal problem")
        log.info(self.thermalSolver.getApplicationSignature())
        #self.thermalSolver._pyroHmacKey = cfg.hkey.encode(encoding='UTF-8')
        self.thermalSolver.solveStep(istep)
        #Get field's uri from thermal application and send it to mechanical application.
        #This prevents copying data to Demo11's computer,
        #mechanical solver will use direct access to thermal field.
        log.info("Thermal problem solved")
        uri = self.thermalSolver.getFieldURI(FieldID.FID_Temperature, self.mechanicalSolver.getAssemblyTime(istep))
        log.info("URI of thermal problem's field is " + str(uri) )
        #field = Pyro4.Proxy(uri)
        #field._pyroHmacKey = cfg.hkey.encode(encoding='UTF-8')
        field = PyroUtil.getObjectFromURI(uri,cfg.hkey)
        self.mechanicalSolver.setField(field)

        #Original version copied data to Demo11's computer and then to thermal solver.
        #This can be time/memory consuming for large data
        #temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
        #self.mechanicalSolver.setField(temperatureField)

        log.info("Solving mechanical problem")
        self.mechanicalSolver.solveStep(istep)
        log.info("URI of mechanical problem's field is " + str(self.mechanicalSolver.getFieldURI(FieldID.FID_Displacement, istep.getTargetTime())) )
        displacementField = self.mechanicalSolver.getField(FieldID.FID_Displacement, istep.getTime())
        # save results as vtk
        temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
        temperatureField.field2VTKData().tofile('temperatureField')
        displacementField.field2VTKData().tofile('displacementField')

        #terminate
        log.info("Time consumed %f s" % (timeT.time()-start))


    def getCriticalTimeStep(self):
        # determine critical time step
        return PQ.PhysicalQuantity(1.0, 's')

    def terminate(self):
        #self.thermalAppRec.terminateAll()
        self.thermalSolver.printMetadata()
        self.thermalSolver.terminate()
        self.thermalJobMan.terminate()
        self.mechanicalSolver.terminate()
        self.mechanicalJobMan.terminate()
        self.appsTunnel.terminate()
        super(Demo11, self).terminate()

    def getApplicationSignature(self):
        return "Demo11 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo11(targetTime=PQ.PhysicalQuantity(1.,'s'))
    demo.initialize()
    demo.solve()
    log.info("Test OK")


