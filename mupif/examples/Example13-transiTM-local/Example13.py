#!/usr/bin/env pythonoun            
import sys
sys.path.extend(['..', '../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ
#from mupif import WorkflowMonitor
import time
import datetime
status = 0


class Demo13(Workflow.Workflow):
    def __init__ (self, targetTime=PQ.PhysicalQuantity(3.,'s')):
        super(Demo13, self).__init__(targetTime=targetTime)
        
        self.thermal = demoapp.thermal_nonstat()
        self.mechanical = demoapp.mechanical()
        self.matPlotFig = None
        
        if (status): # experimental section by bp
            from Config import config
            import Pyro4
            cfg=config(3)
            ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
            uri = ns.lookup(cfg.monitorName)
            self.workflowMonitor = Pyro4.Proxy(uri)
        self.updateStatus('Initialized')
        if (status):
            time.sleep(10)
            
    def initialize(self):
        self.thermal.initialize('inputT13.in','.')
        self.mechanical.initialize('inputM13.in','.')
        
    def solveStep(self, istep, stageID=0, runInBackground=False):
        try:
            self.updateStatus('Running', 0)
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
        self.thermal.printMetadata()
        self.mechanical.printMetadata()
        self.thermal.terminate()
        self.mechanical.terminate()
        self.updateStatus('Finished', 100)

    def getApplicationSignature(self):
        return "Demo13 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo13(targetTime=PQ.PhysicalQuantity(3.0,'s'))
    demo.initialize()
    demo.setMetadata('Execution.Execution_ID','ThermoMech-01')
    demo.setMetadata('Execution.Use_Case_ID','IDThermoMech')
    demo.setMetadata('Execution.Execution_status','Running')
    demo.setMetadata('Execution.Execution_start_date',str(datetime.datetime.now()))
    demo.setMetadata('Execution.Modeling_task_ID','Thermo-mech-1')   
    demo.solve()
    #ft.field2Image2DBlock() #To block the window
    log.info("Test OK")
    demo.setMetadata('Execution.Execution_end_date',str(datetime.datetime.now()))
    demo.setMetadata('Execution.Execution_status','Completed')
    demo.printMetadata()
