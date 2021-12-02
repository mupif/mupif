import sys
sys.path.extend(['..', '../..'])
import mupif as mp
from exconfig import ExConfig
cfg=ExConfig()

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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cummulative time',
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
            value=(0.,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)
        self.retprop = mp.ConstantProperty(
            value=(0.,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)

        try:
            self.app1 = mp.pyroutil.allocateApplicationWithJobManager(
                ns=ns, jobMan=self.jobMan,
                # cfg.jobNatPorts[0],
                # mp.pyroutil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost)
            )
            log.info(self.app1)
        except Exception as e:
            log.exception(e)

            appsig = self.app1.getApplicationSignature()
            log.info("Working application 1 on server " + appsig)

        self.registerModel(self.app1, 'app1')

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        self.app1.initialize(metadata=passingMD)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = mp.ConstantProperty(value=(1000,), propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s)
        self.app1.set(val)
        self.app1.solveStep(istep)
        self.retprop = self.app1.get(mp.DataID.PID_Time, istep.getTime())
        log.info("Sucessfully received " + str(self.retprop.getValue(istep.getTime())))
        
    def terminate(self):    
        self.app1.terminate()
        self.jobMan.terminate()
        super().terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def get(self, objectTypeID, time=None, objectID=0):
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=self.retprop.getValue(time), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        else:
            raise mp.APIError('Unknown property ID')
        
    def set(self, obj, objectID=0):
        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mp.DataID.PID_Time_step:
                # remember the mapped value
                self.contrib = obj
        super().set(obj=obj, objectID=objectID)

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Example04 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    targetTime = 1.*mp.U.s

    demo = Example04()

    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    demo.initialize(metadata=executionMetadata)
    demo.set(mp.ConstantProperty(value=(targetTime,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo.solve()
    kpi = demo.get(mp.DataID.PID_Time, targetTime)
    demo.terminate()
    if kpi.getValue(targetTime)[0] == 1000.:
        log.info("Test OK")
        kpi = 0
        sys.exit(0)
    else:
        log.info("Test FAILED")
        kpi = 0
        sys.exit(1)
