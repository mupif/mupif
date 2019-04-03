#!/usr/bin/env python
import sys
import os
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

class Example08(Workflow.Workflow):
   
    def __init__(self, metaData={}):
        """
        Construct the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """

        MD = {
            'Name': 'Thermo-mechanical non-stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'Non-stationary thermo-mechanical problem using finite elements on rectangular domain',
            'Model_refs_ID': ['NonStatThermo-1', 'Mechanical-1'],
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.FieldID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}]
        }

        super(Example08, self).__init__(metaData=MD)
        self.updateMetadata(metaData)

        self.thermal = None
        self.mechanical = None
        self.thermalJobMan = None
    
    def initialize(self, file='', workdir='', targetTime=PQ.PhysicalQuantity(0., 's'), metaData={}, validateMetaData=True, **kwargs):
        # locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)    
        # connect to JobManager running on (remote) server
        self.thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
        
        try:
            self.thermal = PyroUtil.allocateApplicationWithJobManager(
                ns, self.thermalJobMan,
                cfg.jobNatPorts[0],
                cfg.hkey, PyroUtil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost)
            )
            log.info('Created thermal job')
        except Exception as e:
            log.exception(e)
            self.terminate()
       
        self.mechanical = PyroUtil.connectApp(ns, 'mechanical', cfg.hkey)

        thermalSignature = self.thermal.getApplicationSignature()
        log.info("Working thermal server " + thermalSignature)
        mechanicalSignature = self.mechanical.getApplicationSignature()
        log.info("Working mechanical server " + mechanicalSignature)

        super(Example08, self).initialize(file=file, workdir=workdir, targetTime=targetTime, metaData=metaData, validateMetaData=validateMetaData, **kwargs)

        # To be sure update only required passed metadata in models
        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.thermal.initialize(
            file='..'+os.path.sep+'Example06-stacTM-local'+os.path.sep+'inputT10.in',
            workdir='.',
            metaData=passingMD
        )
        self.mechanical.initialize(
            file='..' + os.path.sep + 'Example06-stacTM-local' + os.path.sep + 'inputM10.in',
            workdir='.',
            metaData=passingMD
        )

        # self.thermal.printMetadata()
        # self.mechanical.printMetadata()

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving thermal problem")
        log.info(self.thermal.getApplicationSignature())
        
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))
        
        self.thermal.solveStep(istep)
        f = self.thermal.getField(FieldID.FID_Temperature, self.mechanical.getAssemblyTime(istep))
        data = f.field2VTKData().tofile('T_%s' % str(istep.getNumber()))

        self.mechanical.setField(f)
        sol = self.mechanical.solveStep(istep) 
        f = self.mechanical.getField(FieldID.FID_Displacement, istep.getTime())
        data = f.field2VTKData().tofile('M_%s' % str(istep.getNumber()))

        self.thermal.finishStep(istep)
        self.mechanical.finishStep(istep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min(self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        if self.thermal is not None:
            self.thermal.terminate()
        if self.thermalJobMan is not None:
            self.thermalJobMan.terminate()
        if self.mechanical is not None:
            self.mechanical.terminate()
        # self.printMetadata()
        super(Example08, self).terminate()
    
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
    demo.initialize(targetTime=PQ.PhysicalQuantity(10., 's'), metaData=workflowMD)
    # demo.printMetadata()
    # print(demo.hasMetadata('Execution.ID'))
    # exit(0)
    demo.solve()
    log.info("Test OK")

