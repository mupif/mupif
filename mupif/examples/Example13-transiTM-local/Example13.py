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
        self.updateStatus('Initialized')
        if (status):
            time.sleep(10)
        self.setMetadata('Workflow.Model_ID','Thermo-mech-1')
        self.setMetadata('Workflow.Model_name','Thermo-mechanical workflow')
        self.setMetadata('Workflow.Model_description','Stationary heat conduction with linear thermoelasticity using finite elements on a rectangular domain')
        self.setMetadata('Workflow.Model_time_lapse','seconds')
        self.setMetadata('Workflow.Model_publication','Felippa: Introduction to finite element methods, 2004')
        self.setMetadata('Workflow.Solver_name','Thermo-mechanical solver')
        self.setMetadata('Workflow.Solver_version_date','1.0, Dec 31 2018')
        self.setMetadata('Workflow.Solver_license','None')
        self.setMetadata('Workflow.Solver_creator','Borek Patzak')
        self.setMetadata('Workflow.Solver_language','Python')
        self.setMetadata('Workflow.Solver_time_step','seconds')
        self.setMetadata('Workflow.Model_boundary_conditions','Dirichlet, Neumann')
        self.setMetadata('Workflow.Workflow_model_reference',[1,2])
        self.setMetadata('Workflow.Accuracy',0.75)
        self.setMetadata('Workflow.Sensitivity','Medium')
        self.setMetadata('Workflow.Complexity','Low')
        self.setMetadata('Workflow.Robustness','High')
        self.setMetadata('Workflow.Estimated_execution cost','0.01€')
        self.setMetadata('Workflow.Estimated_personnel cost','0.01€')
        self.setMetadata('Workflow.Required_expertise','User')
        self.setMetadata('Workflow.Estimated_computational_time','Seconds')
        self.setMetadata('Workflow.Inputs_and_relation_to_Data',['Boundary temperature',1,'Scalar','','Ambient temperature on edges with heat convection'])
        self.setMetadata('Model.Outputs_and_relation_to_Data',[['Displacement field',2,'Vector','Resulting displacement field'], ['Stress field',3,'Vector','Resulting stress field'],['Strain field',4,'Vector','Resulting strain field']])

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
