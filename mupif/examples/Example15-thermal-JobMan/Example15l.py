#!/usr/bin/env pythonoun            
from __future__ import print_function
import sys
# path to demoapp
sys.path.extend(['../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ


class Demo15l(Workflow.Workflow):
    def __init__ (self, targetTime=PQ.PhysicalQuantity(3.,'s')):
        super(Demo15l, self).__init__(file='', workdir='', targetTime=targetTime)
        
        self.thermal = demoapp.thermal('inputT.in','.')
        

    def solveStep(self, istep, stageID=0, runInBackground=False):
        try:
            # solve problem 1
            self.thermal.solveStep(istep)
            # request Temperature from thermal
            ft = self.thermal.getField(FieldID.FID_Temperature, istep.getTime())
            
            data = ft.field2VTKData().tofile('T_local')
            
        except APIError.APIError as e:
            log.error("Following API error occurred:",e)

    def getCriticalTimeStep(self):
        # determine critical time step
        return PQ.PhysicalQuantity(1.0, 's')

    def terminate(self):
        self.thermal.terminate()
        
    def getApplicationSignature(self):
        return "Demo15 local workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo15l(targetTime=PQ.PhysicalQuantity(1.0,'s'))
    demo.solve()
    log.info("Test OK")
