import mupif
import Pyro5
import logging
log = logging.getLogger()


@Pyro5.api.expose
class OOFEMTestWorkflow(mupif.Workflow):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "OOFEMTestWorkflow",
            "ModuleName": "oofem_test_workflow",
            "Name": "OOFEMTestWorkflow",
            "ID": "OOFEM_test_workflow",
            "Description": "",
            "Execution_settings": {
                "Type": "Local"
            },
            "Inputs": [
                {
                    "Name": "edge temperature",
                    "Type": "mupif.Property",
                    "Required": True,
                    "Type_ID": "mupif.DataID.PID_Temperature",
                    "Units": "deg_C",
                    "Obj_ID": [
                        "temperature_top",
                        "temperature_bottom"
                    ],
                    "Set_at": "timestep",
                    "ValueType": "Scalar"
                }
            ],
            "Outputs": [
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "degC"
                },
                {
                    "Name": "displacement",
                    "Type_ID": "mupif.DataID.FID_Displacement",
                    "Type": "mupif.Field",
                    "Units": "m"
                }
            ],
            "Models": [
                {
                    "Name": "thermal",
                    "Jobmanager": "OOFEM_Thermal_demo"
                },
                {
                    "Name": "mechanical",
                    "Jobmanager": "MUPIF_Mechanical_demo"
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=""):
        if obj.isInstance(mupif.Property) and obj.getDataID() == mupif.DataID.PID_Temperature:
            self.getModel('thermal').set(obj, objectID)

    # get method for all external outputs
    def get(self, objectTypeID, time=None, objectID=''):
        if objectTypeID == mupif.DataID.FID_Temperature:
            return self.getModel('thermal').get(objectTypeID=objectTypeID, time=time, objectID=objectID)
        if objectTypeID == mupif.DataID.FID_Displacement:
            return self.getModel('mechanical').get(objectTypeID=objectTypeID, time=time, objectID=objectID)
        if objectTypeID == mupif.DataID.PID_maxDisplacement:
            return self.getModel('mechanical').get(objectTypeID=objectTypeID, time=time, objectID=objectID)
        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        self.getModel('thermal').solveStep(tstep)
        self.getModel('thermal').finishStep(tstep)

        self.getModel('mechanical').set(self.getModel('thermal').get(objectTypeID=mupif.DataID.FID_Temperature))
        self.getModel('mechanical').solveStep(tstep)
        self.getModel('mechanical').finishStep(tstep)


if __name__ == '__main__':
    w = OOFEMTestWorkflow()
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    w.initialize(metadata=md)
    
    ttop = mupif.ConstantProperty(value=300., propID=mupif.DataID.PID_Temperature, valueType=mupif.ValueType.Scalar, unit=mupif.U.deg_C, time=None)
    tbottom = mupif.ConstantProperty(value=-300., propID=mupif.DataID.PID_Temperature, valueType=mupif.ValueType.Scalar, unit=mupif.U.deg_C, time=None)
    w.set(ttop, 'temperature_top')
    w.set(tbottom, 'temperature_bottom')
    
    w.solve()

    tf = w.get(objectTypeID=mupif.DataID.FID_Temperature)
    df = w.get(objectTypeID=mupif.DataID.FID_Displacement)
    max_w = w.get(objectTypeID=mupif.DataID.PID_maxDisplacement)
    w.terminate()

    print(max_w)
    tf.plot2D(fileName='ft.png')
    df.plot2D(fileName='fd.png', fieldComponent=1)
