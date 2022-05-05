import sys
sys.path.extend(['..', '../..'])
import mupif as mp

import logging
log = logging.getLogger()

import time as timeT
start = timeT.time()

log.info('Timer started')


class Example04(mp.Workflow):
   
    def __init__(self, metadata=None):
        MD = {
            'Name': 'Simple application cummulating time steps',
            'ID': 'N/A',
            'Description': 'Cummulates time steps',
            # 'Dependencies': ['SimulationTimer-1'],
            'Version_date': '1.0.0, Feb 2019',
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep", "ValueType": "Scalar"}
            ],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated', "ValueType": "Scalar"}
            ],
            'Models': [
                {
                    'Name': 'm1',
                    'Jobmanager': 'mupif/example04/jobMan'
                }
            ]
        }

        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

        self.contrib = mp.ConstantProperty(
            value=0., propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)
        self.retprop = mp.ConstantProperty(
            value=0., propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        val = mp.ConstantProperty(value=1000, propID=mp.DataID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s)
        self.getModel('m1').set(val)
        self.getModel('m1').solveStep(istep)
        self.retprop = self.getModel('m1').get(mp.DataID.PID_Time, istep.getTime())
        log.info("Sucessfully received " + str(self.retprop.getValue(istep.getTime())))
        
    def terminate(self):
        super().terminate()
        log.info("Time elapsed %f s" % (timeT.time()-start))

    def get(self, objectTypeID, time=None, objectID=""):
        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=self.retprop.getValue(time), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time)
        else:
            raise mp.APIError('Unknown property ID')
        
    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mp.DataID.PID_Time_step:
                # remember the mapped value
                self.contrib = obj
        super().set(obj=obj, objectID=objectID)

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Example04 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


if __name__ == '__main__':
    targetTime = 1.*mp.U.s

    demo = Example04()

    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    demo.initialize(metadata=executionMetadata)
    demo.set(mp.ConstantProperty(value=targetTime, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')
    demo.solve()
    kpi = demo.get(mp.DataID.PID_Time, targetTime)
    demo.terminate()
    if kpi.getValue(targetTime) == 1000.:
        log.info("Test OK")
        kpi = 0
        sys.exit(0)
    else:
        log.info("Test FAILED")
        kpi = 0
        sys.exit(1)
