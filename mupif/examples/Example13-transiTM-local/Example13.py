#!/usr/bin/env pythonoun            
from __future__ import print_function
import sys
sys.path.extend(['../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

# enable to see plots
graphics = False

class Demo13(Workflow.Workflow):
    def __init__ (self, targetTime=PQ.PhysicalQuantity(3.,'s')):
        super(Demo13, self).__init__(file='', workdir='', targetTime=targetTime)
        
        self.thermal = demoapp.thermal_nonstat('inputT13.in','.')
        self.mechanical = demoapp.mechanical('inputM13.in', '.')
        self.matPlotFig = None


    def solveStep(self, istep, stageID=0, runInBackground=False):
        try:
            # solve problem 1
            self.thermal.solveStep(istep)
            # request Temperature from thermal
            ft = self.thermal.getField(FieldID.FID_Temperature, istep.getTime())
            
            self.mechanical.setField(self.thermal.getField(FieldID.FID_Temperature,
                                                           self.mechanical.getAssemblyTime(istep)))
            sol = self.mechanical.solveStep(istep) 
            f = self.mechanical.getField(FieldID.FID_Displacement, istep.getTime())

            data = f.field2VTKData().tofile('M_%s'%str(istep.getNumber()))
            if (graphics):
                self.matPlotFig = f.field2Image2D(title='Mechanical ' + str(istep.getTime().inUnitsOf(timeUnits).getValue()), barRange=(-9e-5, 1.6e-6), fileName='mechanical.png', fieldComponent=1, figsize = (12,6), matPlotFig=self.matPlotFig) 
            
        except APIError.APIError as e:
            log.error("Following API error occurred:",e)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min (self.thermal.getCriticalTimeStep(), self.mechanical.getCriticalTimeStep())

    def terminate(self):
        self.thermal.terminate()
        self.mechanical.terminate()

    def getApplicationSignature(self):
        return "Demo13 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo13(targetTime=PQ.PhysicalQuantity(3.0,'s'))
    demo.solve()
    #ft.field2Image2DBlock() #To block the window
    log.info("Test OK")
