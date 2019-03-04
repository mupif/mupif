#!/usr/bin/env python
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)
import logging
log = logging.getLogger()

import time as timeTime
start = timeTime.time()
log.info('Timer started')
import mupif.Physics.PhysicalQuantities as PQ


# localize JobManager running on (remote) server and create a tunnel to it
# allocate the thermal server
# solverJobManRecNoSSH = (cfg.serverPort, cfg.serverPort, cfg.server, '', cfg.jobManName)

class Demo16(Workflow.Workflow):
   
    def __init__(self, targetTime=PQ.PhysicalQuantity(0., 's')):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        super(Demo16, self).__init__(targetTime=targetTime)
    
    def initialize(self, file='', workdir='', executionID='', metaData={}, **kwargs):    
        # locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)    
        # connect to JobManager running on (remote) server
        self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
        self.thermal = None
        self.mechanical = None
        
        try:
            self.thermal = PyroUtil.allocateApplicationWithJobManager( ns, self.thermalJobMan, cfg.jobNatPorts[0], cfg.hkey, PyroUtil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
            log.info('Created thermal job')
        except Exception as e:
            log.exception(e)
       
        self.mechanical = PyroUtil.connectApp(ns, 'mechanical', cfg.hkey)
       
        thermalSignature=self.thermal.getApplicationSignature()
        log.info("Working thermal server " + thermalSignature)
        mechanicalSignature=self.mechanical.getApplicationSignature()
        log.info("Working mechanical server " + mechanicalSignature)
        
        metaData = {
            'Name': 'Thermo-mechanical non-stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'Non-stationary thermo-mechanical problem using finite elements on rectangular domain',
            'Model_refs_ID': ['NonStatThermo-1', 'Mechanical-1'],
            'Boundary_conditions': 'Dirichlet, Neumann, Cauchy',
            'Input_types': [],
            'Output_types': [
                {'ID': 'N/A', 'Name': 'Displacement field', 'Description': 'Displacement field on 2D domain',
                 'Units': 'm', 'Type': 'Field', 'Type_ID': 'mupif.FieldID.FID_Displacement'}],
            'Solver': {
                'Accuracy': 'Medium',
                'Sensitivity': 'Low',
                'Complexity': 'Low',
                'Robustness': 'High',
                'Estim_time_step': 1,
                'Estim_comp_time': 1.e-3,
                'Estim_execution_cost': 0.01,
                'Estim_personnel_cost': 0.01,
                'Required_expertise': 'None',
                'Language': 'Python',
                'License': 'LGPL',
                'Creator': 'Borek Patzak',
                'Version_date': '1.0.0, Feb 2019',
                'Documentation': 'Felippa: Introduction to finite element methods, 2004',
            }
        }

        super().initialize(file, workdir, executionID, metaData, **kwargs)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving thermal problem")
        log.info(self.thermal.getApplicationSignature())
        
        log.debug("Step: %g %g %g"%(istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        self.thermal.solveStep(istep)
        f = self.thermal.getField(FieldID.FID_Temperature, self.mechanical.getAssemblyTime(istep))
        data = f.field2VTKData().tofile('T_%s'%str(istep.getNumber()))

        self.mechanical.setField(f)
        sol = self.mechanical.solveStep(istep) 
        f = self.mechanical.getField(FieldID.FID_Displacement, istep.getTime())
        data = f.field2VTKData().tofile('M_%s'%str(istep.getNumber()))

        self.thermal.finishStep(istep)
        self.mechanical.finishStep(istep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min (self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        self.thermal.printMetadata()
        self.mechanical.printMetadata()
        self.thermal.terminate()
        self.thermalJobMan.terminate()
        self.mechanical.terminate()
        self.printMetadata()
        super(Demo16, self).terminate()
    
    def getApplicationSignature(self):
        return "Demo16 workflow 1.0 - Thermo-mechanical non-stationary problem"

    def getAPIVersion(self):
        return "1.0"


if __name__=='__main__':
    demo = Demo16(targetTime=PQ.PhysicalQuantity(10.,'s'))
    demo.initialize()
    demo.solve()
    log.info("Test OK")

