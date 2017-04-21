#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import mupif
import conf_vpn as cfg


class Demo18(Workflow.Workflow):
   
    def __init__ (self, targetTime=0.):
        super(Demo18, self).__init__(file='', workdir='', targetTime=targetTime)
        
        #locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
        #localize JobManager running on (remote) server and create a tunnel to it
        #allocate the thermal server
        solverJobManRecNoSSH = (cfg.serverPort, cfg.serverPort, cfg.server, '', cfg.jobManName)

        jobNatport = -1

        try:
            #self.thermalAppRec = PyroUtil.allocateApplicationWithJobManager( ns, solverJobManRecNoSSH, jobNatport, sshClient='ssh', options='', sshHost = '' )
            self.thermalAppRec = PyroUtil.allocateApplicationWithJobManager( ns, cfg.jobManName, jobNatport, userName='', sshClient='ssh', options='', sshHost = '' )
            mupif.log.info("Allocated application %s" % self.thermalAppRec)
            self.thermal = self.thermalAppRec.getApplication()
        except Exception as e:
            mupif.log.exception(e)

        appsig=self.thermal.getApplicationSignature()
        mupif.log.info("Working thermal server " + appsig)
        self.mechanical = PyroUtil.connectApp(ns, 'mechanical')
        appsig=self.mechanical.getApplicationSignature()
        mupif.log.info("Working mechanical server " + appsig)


    def solveStep(self, istep, stageID=0, runInBackground=False):

        self.thermal.solveStep(istep)
        f = self.thermal.getField(FieldID.FID_Temperature, istep.getTime())
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
        
        self.thermalAppRec.terminateAll()
        self.mechanical.terminate()
        super(Demo18, self).terminate()

    def getApplicationSignature(self):
        return "Demo18 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


    
if __name__=='__main__':
    demo = Demo18(targetTime=10.)
    demo.solve()


