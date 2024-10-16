import sys
sys.path.extend(['.', '..', '../..'])

import mupif as mp
import logging
log = logging.getLogger()


class Example11(mp.Workflow):
   
    def __init__(self, metadata=None):
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
            'Outputs': [],
            'Models': [
                {
                    'Name': 'm1',
                    'Module': 'model1',
                    'Class': 'Model1',
                },
                {
                    'Name': 'm2',
                    'Module': 'model2',
                    'Class': 'Model2',
                }
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
    
    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving workflow")    
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))

        try:
            # solve problem 1
            self.getModel('m1').solveStep(istep)
            # handshake the data
            grainState = self.getModel('m1').get(mp.DataID.ID_GrainState, self.getModel('m1').getAssemblyTime(istep))
            self.getModel('m2').set(grainState)
            self.getModel('m2').solveStep(istep)
            grainState2 = self.getModel('m2').get(mp.DataID.ID_GrainState, self.getModel('m1').getAssemblyTime(istep))

        except mp.apierror.APIError as e:
            log.error("Following API error occurred: %s" % e)
    
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
    workflow.initialize(metadata=workflowMD)
    workflow.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    workflow.solve()
    workflow.terminate()
