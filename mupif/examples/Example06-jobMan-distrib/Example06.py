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

import time as timeT
start = timeT.time()

log.info('Timer started')

class Demo06(Workflow.Workflow):
   
    def __init__ (self, targetTime=0.):
        super(Demo06, self).__init__(file='', workdir='', targetTime=targetTime)
        
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

    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = Property.Property(1000, PropertyID.PID_Demo_Value, ValueType.Scalar, 0.0, None)
        self.app1.setProperty (val)
        self.app1.solveStep(None)
        retProp = self.app1.getProperty(PropertyID.PID_Demo_Value, istep)
        log.info("Sucessfully received " + str(retProp.getValue()))
        
    def terminate(self):    
        log.info("Terminating " + str(self.app1.getURI()))
        self.app1.terminate()
        self.jobMan.terminate
        super(Demo06, self).terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def getApplicationSignature(self):
        return "Demo06 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"
    
if __name__=='__main__':
    demo = Demo06()
    demo.solve()
    log.info("Test OK")


