import sys
sys.path.extend(['..', '../..'])
import mupif as mp
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[mp.util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)

import logging
log = logging.getLogger()

import time as timeT
start = timeT.time()

log.info('Timer started')


class Example04(mp.Workflow):
   
    def __init__(self, metadata={}):
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

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        
        # locate nameserver
        ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
        # connect to JobManager running on (remote) server and create a tunnel to it
        self.jobMan = mp.pyroutil.connectJobManager(ns, cfg.jobManName)
        log.info('Connected to JobManager')
        self.app1 = None
        self.contrib = mp.ConstantProperty(
            value=(0.,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.Q.s)
        self.retprop = mp.ConstantProperty(
            value=(0.,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.Q.s)

        try:
            self.app1 = mp.pyroutil.allocateApplicationWithJobManager(
                ns, self.jobMan, cfg.jobNatPorts[0],
                mp.pyroutil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost)
            )
            log.info(self.app1)
        except Exception as e:
            log.exception(e)

            appsig = self.app1.getApplicationSignature()
            log.info("Working application 1 on server " + appsig)

        self.registerModel(self.app1, 'app1')

    def initialize(self, file='', workdir='', targetTime=1*mp.Q.s, metadata={}, validateMetaData=False):
        # FIXME: validate metadata
        super().initialize(targetTime=targetTime, metadata=metadata,validateMetaData=validateMetaData)

        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        self.app1.initialize(metadata=passingMD)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = mp.ConstantProperty(value=(1000,), propID=mp.PropertyID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s)
        self.app1.setProperty(val)
        self.app1.solveStep(istep)
        self.retprop = self.app1.getProperty(mp.PropertyID.PID_Time, istep.getTime())
        log.info("Sucessfully received " + str(self.retprop.getValue(istep.getTime())))
        
    def terminate(self):    
        self.app1.terminate()
        self.jobMan.terminate()
        super(Example04, self).terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def getProperty(self, propID, time, objectID=0):
        if propID == mp.PropertyID.PID_Time:
            return mp.ConstantProperty(value=self.retprop.getValue(time), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        else:
            raise mp.APIError('Unknown property ID')
        
    def setProperty(self, prop, objectID=0):
        if prop.getPropertyID() == mp.PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = prop
        else:
            raise mp.APIError('Unknown property ID')

    def getCriticalTimeStep(self):
        return 1*mp.Q.s

    def getApplicationSignature(self):
        return "Example04 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    targetTime = 1*mp.Q.s

    demo = Example04()

    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    demo.initialize(targetTime=targetTime, metadata=executionMetadata)

    demo.solve()
    kpi = demo.getProperty(mp.PropertyID.PID_Time, targetTime)
    demo.terminate()
    if kpi.getValue(targetTime)[0] == 1000.:
        log.info("Test OK")
        kpi = 0
        sys.exit(0)
    else:
        log.info("Test FAILED")
        kpi = 0
        sys.exit(1)
