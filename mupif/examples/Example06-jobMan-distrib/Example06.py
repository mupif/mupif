import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)
import mupif.Physics.PhysicalQuantities as PQ

import logging
log = logging.getLogger()

import time as timeT
start = timeT.time()

log.info('Timer started')

class Demo06(Workflow.Workflow):
   
    def __init__ (self, targetTime=PQ.PhysicalQuantity('1 s')):
        super(Demo06, self).__init__(targetTime=targetTime)
        
        #locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
        #connect to JobManager running on (remote) server and create a tunnel to it
        self.jobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
        log.info('Connected to JobManager')
        self.app1 = None

        try:
            self.app1 = PyroUtil.allocateApplicationWithJobManager( ns, self.jobMan, cfg.jobNatPorts[0], cfg.hkey, PyroUtil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost ) )
            log.info(self.app1)
        except Exception as e:
            log.exception(e)

            appsig=self.app1.getApplicationSignature()
            log.info("Working application 1 on server " + appsig)

    def initialize(self):
        MD = { 'Model.Model_description' : 'Computes the average of time' }
        super().initialize(metaData=MD)
        MD = { 'Model.Model_description' : 'Computes the average of time' }
        self.app1.initialize(metaData=MD)
    
    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = Property.ConstantProperty(1000, PropertyID.PID_Concentration, ValueType.Scalar, 'kg/m**3')
        self.app1.setProperty (val)
        self.app1.solveStep(istep)
        self.retprop = self.app1.getProperty(PropertyID.PID_CumulativeConcentration, istep.getTime())
        log.info("Sucessfully received " + str(self.retprop.getValue(istep.getTime())))
        
    def terminate(self):    
        self.app1.terminate()
        self.jobMan.terminate()
        super(Demo06, self).terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_KPI01):
            return Property.ConstantProperty(self.retprop.getValue(time), PropertyID.PID_KPI01, ValueType.Scalar, 'kg/m**3', time)
        else:
            raise APIError.APIError ('Unknown property ID')
        
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property
        else:
            raise APIError.APIError ('Unknown property ID')


    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0,'s')
    def getApplicationSignature(self):
        return "Demo06 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"
    
if __name__=='__main__':
    targetTime=PQ.PhysicalQuantity('1 s')
    demo = Demo06(targetTime)
    demo.solve()
    kpi = demo.getProperty(PropertyID.PID_KPI01, targetTime)
    demo.terminate()
    if (kpi.getValue(targetTime) == 1000):
        log.info("Test OK")
        kpi = 0
        sys.exit(0)
    else:
        log.info("Test FAILED")
        kpi = 0
        sys.exit(1)


