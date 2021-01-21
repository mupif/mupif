import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)
import mupif.physics.physicalquantities as PQ

import logging
log = logging.getLogger()

import time as timeT
start = timeT.time()

log.info('Timer started')


class Example04(workflow.Workflow):
   
    def __init__(self, metaData={}):
        MD = {
            'Name': 'Simple application cummulating time steps',
            'ID': 'N/A',
            'Description': 'Cummulates time steps',
            'Dependencies': ['SimulationTimer-1'],
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }

        super(Example04, self).__init__(metaData=MD)
        self.updateMetadata(metaData)
        
        # locate nameserver
        ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
        # connect to JobManager running on (remote) server and create a tunnel to it
        self.jobMan = pyroutil.connectJobManager(ns, cfg.jobManName)
        log.info('Connected to JobManager')
        self.app1 = None
        self.contrib = property.ConstantProperty(
            (0.,), PropertyID.PID_Time, ValueType.Scalar, 's', PQ.PhysicalQuantity(0., 's'))
        self.retprop = property.ConstantProperty(
            (0.,), PropertyID.PID_Time, ValueType.Scalar, 's', PQ.PhysicalQuantity(0., 's'))

        try:
            self.app1 = pyroutil.allocateApplicationWithJobManager(
                ns, self.jobMan, cfg.jobNatPorts[0],
                pyroutil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost)
            )
            log.info(self.app1)
        except Exception as e:
            log.exception(e)

            appsig = self.app1.getApplicationSignature()
            log.info("Working application 1 on server " + appsig)

        self.registerModel(self.app1, 'app1')

    def initialize(self, file='', workdir='', targetTime=PQ.PhysicalQuantity('1 s'), metaData={}, validateMetaData=True, **kwargs):
        super().initialize(targetTime=targetTime, metaData=metaData)

        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        self.app1.initialize(metaData=passingMD)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = property.ConstantProperty((1000,), PropertyID.PID_Time_step, ValueType.Scalar, 's')
        self.app1.setProperty(val)
        self.app1.solveStep(istep)
        self.retprop = self.app1.getProperty(PropertyID.PID_Time, istep.getTime())
        log.info("Sucessfully received " + str(self.retprop.getValue(istep.getTime())))
        
    def terminate(self):    
        self.app1.terminate()
        self.jobMan.terminate()
        super(Example04, self).terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def getProperty(self, propID, time, objectID=0):
        if propID == PropertyID.PID_Time:
            return property.ConstantProperty(self.retprop.getValue(time), PropertyID.PID_Time, ValueType.Scalar, 's', time)
        else:
            raise apierror.APIError('Unknown property ID')
        
    def setProperty(self, property, objectID=0):
        if property.getPropertyID() == PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = property
        else:
            raise apierror.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')

    def getApplicationSignature(self):
        return "Example04 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    targetTime = PQ.PhysicalQuantity('1 s')

    demo = Example04()

    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    demo.initialize(targetTime=targetTime, metaData=executionMetadata)

    demo.solve()
    kpi = demo.getProperty(PropertyID.PID_Time, targetTime)
    demo.terminate()
    if kpi.getValue(targetTime)[0] == 1000.:
        log.info("Test OK")
        kpi = 0
        sys.exit(0)
    else:
        log.info("Test FAILED")
        kpi = 0
        sys.exit(1)
