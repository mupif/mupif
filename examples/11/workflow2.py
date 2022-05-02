import sys
sys.path.extend(['.', '..', '../..'])

import mupif as mp
import logging
log = logging.getLogger()


class Example11_2(mp.Workflow):
   
    def __init__(self, metadata={}):
        """
        Construct the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """

        MD = {
            'Name': 'Grain state molecule replacement demo workflow',
            'ID': 'RW1',
            'Description': 'Simple workflow to demonstrate molecule replacement in grain state',
            'Version_date': '1.0.0, May 2021',
            'Inputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state', 'Description': 'Initial grain state', 'Units': 'None', 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep"}
            ],
            'Outputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state', 'Description': 'Updated grain state with dopant', 'Units': 'None', 'Origin': 'Simulated'}
            ],
            'Models': [
                {
                    'Name': 'm2',
                    'Module': 'model2',
                    'Class': 'Model2',
                }
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
    
    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        
        log.info("Solving workflow")    
        log.debug("Step: %g %g %g" % (istep.getTime().getValue(), istep.getTimeIncrement().getValue(), istep.number))

        try:
            self.getModel('m2').solveStep(istep)

        except mp.apierror.APIError as e:
            log.error("Following API error occurred: %s" % e)

    def get(self, objectTypeID, time=None, objectID=""):
        return self.getModel('m2').get(objectTypeID, time, objectID)

    def set(self, obj, objectID=""):
        return self.getModel('m2').set(obj, objectID)
    
    def getApplicationSignature(self):
        return "Example11 workflow2 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    workflow = Example11_2()
    workflowMD = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    workflow.initialize(metadata=workflowMD)
    workflow.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    gs_in = mp.heavystruct.HeavyStruct(h5path='./data1.h5', id=mp.dataid.DataID.ID_GrainState)
    workflow.set(gs_in)
    workflow.solve()
    gs_out = workflow.get(mp.DataID.ID_GrainState)
    gs_out.cloneHandle('./data2.h5')

    workflow.terminate()
