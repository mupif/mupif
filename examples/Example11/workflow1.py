import sys
sys.path.extend(['.', '..', '../..'])

import mupif as mp
import logging
log = logging.getLogger()

from model1 import Model1


class Example11_1(mp.workflow.Workflow):
   
    def __init__(self, metadata={}):
        """
        Construct the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """

        MD = {
            'Name': 'Grain state generator demo workflow',
            'ID': 'RW1',
            'Description': 'Simple workflow to demonstrate molecule replacement in grain state',
            'Version_date': '1.0.0, May 2021',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state', 'Description': 'Sample Random grain state', 'Units': 'None', 'Origin': 'Simulated'}
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        # model references
        self.m1 = None
    
    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
    
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)
        self.m1 = Model1()

        # To be sure update only required passed metadata in models
        passingMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        self.m1.initialize(metadata=passingMD)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving workflow")    
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))

        try:
            self.m1.solveStep(istep)

        except mp.apierror.APIError as e:
            log.error("Following API error occurred: %s" % e)

    def finishStep(self, tstep):
        self.m1.finishStep(tstep)

    def get(self, objectTypeID, time=None, objectID=0):
        return self.m1.get(objectTypeID, time, objectID)

    def set(self, obj, objectID=0):
        return self.m1.set(obj, objectID)

    def getCriticalTimeStep(self):
        return self.m1.getCriticalTimeStep()

    def terminate(self):
        if self.m1 is not None:
            self.m1.terminate()
        super().terminate()
    
    def getApplicationSignature(self):
        return "Example11 workflow1 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    workflow = Example11_1()
    workflowMD = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    workflow.initialize(metadata=workflowMD)
    workflow.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    workflow.solve()
    gs = workflow.get(mp.DataID.ID_GrainState)
    gs.cloneHandle('./data1.h5')
    workflow.terminate()
