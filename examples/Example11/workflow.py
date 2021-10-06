import sys
sys.path.extend(['.', '..', '../..'])

import mupif as mp
import logging
log = logging.getLogger()

from model1 import Model1
from model2 import Model2


class Example11(mp.workflow.Workflow):
   
    def __init__(self, metadata={}):
        """
        Construct the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """

        MD = {
            'Name': 'Molecule replacement demo workflow',
            'ID': 'RW1',
            'Description': 'Simple workflow to demonstrate molecule replacement in grain state',
            'Version_date': '1.0.0, May 2021',
            'Inputs': [],
            'Outputs': []
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        # model references
        self.m1 = None
        self.m2 = None
    
    def initialize(self, workdir='', targetTime=0*mp.U.s, metadata={}, validateMetaData=True):
    
        super().initialize(workdir=workdir, targetTime=targetTime, metadata=metadata, validateMetaData=validateMetaData)
        self.m1 = Model1()
        self.m2 = Model2()

        # To be sure update only required passed metadata in models
        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.m1.initialize(metadata=passingMD)
        self.m2.initialize(metadata=passingMD)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving workflow")    
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))

        try:
            # solve problem 1
            self.m1.solveStep(istep)
            # handshake the data
            grainState = self.m1.get(mp.DataID.PID_GrainState, self.m1.getAssemblyTime(istep))
            self.m2.set(grainState)
            self.m2.solveStep(istep)
            grainState2 = self.m2.get(mp.DataID.PID_GrainState, self.m1.getAssemblyTime(istep))

        except mp.apierror.APIError as e:
            log.error("Following API error occurred: %s" % e)

    def finishStep(self, tstep):
        self.m1.finishStep(tstep)
        self.m2.finishStep(tstep)

    def getCriticalTimeStep(self):
        # determine critical time step
        return min(self.m1.getCriticalTimeStep(), self.m2.getCriticalTimeStep())

    def terminate(self):
        if self.m1 is not None:
            self.m1.terminate()
        if self.m2 is not None:
            self.m2.terminate()
        super().terminate()
    
    def getApplicationSignature(self):
        return "Example11 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    workflow = Example11()
    workflowMD = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    workflow.initialize(targetTime=1*mp.U.s, metadata=workflowMD)
    workflow.solve()
    workflow.terminate()
