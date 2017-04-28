from __future__ import print_function
import sys
sys.path.append('../../..')
import demoapp
import meshgen
from mupif import *


class Demo10(Workflow.Workflow):
    """
    Class representing Demo10 workflow
    """
    def __init__(self, targetTime=1.0):
        """
        No special code here, as this is stationary, one step, workflow
        """
        super(Demo10, self).__init__(file='', workdir='', targetTime=targetTime)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        if True:
            app = demoapp.thermal('inputT.in','.')
            print(app.getApplicationSignature())
            
            sol = app.solveStep(TimeStep.TimeStep(0,1)) 
            f = app.getField(FieldID.FID_Temperature, 0.0)
            data = f.field2VTKData().tofile('example2')

        if True:
            app2 = demoapp.mechanical('inputM.in', '.')
            print(app2.getApplicationSignature())
            
            app2.setField(f)
            sol = app2.solveStep(TimeStep.TimeStep(0,1)) 
            f = app2.getField(FieldID.FID_Displacement, 0.0)
            data = f.field2VTKData().tofile('example3')
    
    def getCriticalTimeStep(self):
        # determine critical time step
        return 1.0

    def terminate(self):
        super(Demo10, self).terminate()

    def getApplicationSignature(self):
        return "Demo10 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


    
if __name__=='__main__':
    demo = Demo10(targetTime=1.)
    demo.solve()
