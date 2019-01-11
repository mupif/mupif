#!/usr/bin/env pythonoun            
import sys
sys.path.extend(['..', '../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ
from   mupif import WorkflowMonitor
import time
status = 0


class Demo13(Workflow.Workflow):
    def __init__ (self, targetTime=PQ.PhysicalQuantity(3.,'s')):
        super(Demo13, self).__init__(file='', workdir='', targetTime=targetTime)
        
        self.thermal = demoapp.thermal_nonstat('inputT13.in','.')
        self.mechanical = demoapp.mechanical('inputM13.in', '.')
        self.matPlotFig = None
        
        if (status): # experimental section by bp
            from Config import config
            import Pyro4
            cfg=config(3)
            ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
            uri = ns.lookup(cfg.monitorName)
            self.workflowMonitor = Pyro4.Proxy(uri)
        self.updateStaus(WorkflowMonitor.WorkflowMonitorStatus.Initialized)     
        if (status):
            time.sleep(10)


    def solveStep(self, istep, stageID=0, runInBackground=False):
        try:
            self.updateStaus(WorkflowMonitor.WorkflowMonitorStatus.Running, 0)
            if (status):
                time.sleep(10)
            # solve problem 1
            self.thermal.solveStep(istep)
            # request Temperature from thermal
            ft = self.thermal.getField(FieldID.FID_Temperature, istep.getTime())

            #self.matPlotFig = ft.field2Image2D()
            #ft.field2Image2DBlock()  # To block the window

            self.mechanical.setField(self.thermal.getField(FieldID.FID_Temperature,
                                                           self.mechanical.getAssemblyTime(istep)))
            sol = self.mechanical.solveStep(istep) 
            f = self.mechanical.getField(FieldID.FID_Displacement, istep.getTime())

            data = f.field2VTKData().tofile('M_%s'%str(istep.getNumber()))

        except APIError.APIError as e:
            log.error("Following API error occurred:"+str(e))

    def getCriticalTimeStep(self):
        # determine critical time step
        return min (self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        self.thermal.terminate()
        self.mechanical.terminate()
        self.updateStaus(WorkflowMonitor.WorkflowMonitorStatus.Finished, 100)

    def getApplicationSignature(self):
        return "Demo13 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo13(targetTime=PQ.PhysicalQuantity(3.0,'s'))
    demo.solve()
    #ft.field2Image2DBlock() #To block the window
    log.info("Test OK")
