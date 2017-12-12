#!/usr/bin/env python
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)
import logging
log = logging.getLogger()

import time as timeTime
start = timeTime.time()
log.info('Timer started')
import mupif.Physics.PhysicalQuantities as PQ


#localize JobManager running on (remote) server and create a tunnel to it
#allocate the thermal server
#solverJobManRecNoSSH = (cfg.serverPort, cfg.serverPort, cfg.server, '', cfg.jobManName)

class Demo16(Workflow.Workflow):
   
    def __init__ (self, targetTime=PQ.PhysicalQuantity(0.,'s')):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        super(Demo16, self).__init__(file='', workdir='', targetTime=targetTime)
        #locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)    
        #connect to JobManager running on (remote) server
        self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
        self.thermal = None
        self.mechanical = None
        
        try:
            self.thermal = PyroUtil.allocateApplicationWithJobManager( ns, self.thermalJobMan, cfg.jobNatPorts[0], cfg.hkey, PyroUtil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
            log.info('Created thermal job')
        except Exception as e:
            log.exception(e)
       
        self.mechanical = PyroUtil.connectApp(ns, 'mechanical')
       
        thermalSignature=self.thermal.getApplicationSignature()
        log.info("Working thermal server " + thermalSignature)
        mechanicalSignature=self.mechanical.getApplicationSignature()
        log.info("Working mechanical server " + mechanicalSignature)
        
    def solveStep(self, istep, stageID=0, runInBackground=False):
        log.info("Solving thermal problem")
        log.info(self.thermal.getApplicationSignature())
        
        log.debug("Step: %g %g %g"%(istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        self.thermal.solveStep(istep)
        f = self.thermal.getField(FieldID.FID_Temperature, istep.getTargetTime())
        data = f.field2VTKData().tofile('T_%s'%str(istep.getNumber()))

        self.mechanical.setField(f)
        sol = self.mechanical.solveStep(istep) 
        f = self.mechanical.getField(FieldID.FID_Displacement, istep.getTargetTime())
        data = f.field2VTKData().tofile('M_%s'%str(istep.getNumber()))

        self.thermal.finishStep(istep)
        self.mechanical.finishStep(istep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min (self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        #self.thermalAppRec.terminateAll()
        self.thermal.terminate()
        self.thermalJobMan.terminate()
        self.mechanical.terminate()
        super(Demo16, self).terminate()
    
    def getApplicationSignature(self):
        return "Demo16 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

if __name__=='__main__':
    demo = Demo16(targetTime=PQ.PhysicalQuantity(10.,'s'))
    demo.solve()
    log.info("Test OK")




