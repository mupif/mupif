import Pyro5
import sys
sys.path.extend(['.', '..', '../..'])
import mupif as mp
from mupif import pyroutil
import logging
log = logging.getLogger()


class Example15(mp.Workflow):
   
    def __init__(self, metadata=None):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        MD = {
            'Name': 'Thermo-mechanical non-stationary problem',
            'ID': 'Thermo-mechanical-1',
            'Description': 'Non-stationary thermo-mechanical problem using finite elements on rectangular domain',
            # 'Dependencies' are generated automatically
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Displacement', 'Name': 'Displacement field',
                 'Description': 'Displacement field on 2D domain', 'Units': 'm'}
            ],
            'Models': [
                {
                    'Name': 'model',
                    'Jobmanager': 'Mupif.JobManager@ThermalSolver-ex07'
                }
            ],
            'ExecutionProfiles': [
                {
                    'Name': 'Execution profile 1',
                    'Cost': '$$',
                    'Description': 'Description of Execution profile 1',
                    'Models': [
                        {
                            'Name': 'model',
                            'RequiredModelMetadata': set(), # empty set
                            'OptionalModelMetadata': {'Accuracy_high'}
                        }
                    ]
                },
                {
                    'Name': 'Execution profile 2',
                    'Cost': '$',
                    'Description': 'Description of Execution profile 2',
                    'Models': [
                        {
                            'Name': 'model',
                            'RequiredModelMetadata': {'Runtime_seconds'},
                            'OptionalModelMetadata': {'Accuracy_high'}
                        }
                    ]
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        # locate nameserver
        ns = pyroutil.connectNameserver()
        self.daemon = pyroutil.getDaemon(ns)
        print(self._models)

        log.info("Working thermal solver on server " + self.getModel('model').getApplicationSignature())

    def solveStep(self, istep, stageID=0, runInBackground=False):
        pass
        

    def getCriticalTimeStep(self):
        # determine critical time step
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__ == '__main__':

    ns = mp.pyroutil.connectNameserver()
    pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}).getApplicationSignature()

    print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}, optionalMData={'Runtime_seconds'}).getModelMetadata()['ID'])
    print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}, optionalMData={'Runtime_minutes'}).getModelMetadata()['ID'])
    print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model', 'Accuracy_Medium'}, optionalMData={'Runtime_minutes'}).getModelMetadata()['ID'])
    print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model', 'Runtime_minutes'}, optionalMData={'Accuracy_high'}).getModelMetadata()['ID'])

    demo = Example15()
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1',
            'ExecutionProfileIndx': 1
        }
    }
    demo.initialize(metadata=md)
    demo.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo.solve()
    demo.printListOfModels()
    demo.terminate()
    log.info("Test OK")
    print("OK")

    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1',
            'ExecutionProfileIndx': 0
        }
    }
    demo2 = Example15()
    demo2.initialize(metadata=md)
    demo2.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo2.solve()
    demo2.printListOfModels()
    demo2.terminate()
    log.info("Test OK")
    print("OK")



