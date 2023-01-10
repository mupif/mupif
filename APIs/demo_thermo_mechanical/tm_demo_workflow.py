import mupif
import copy
import Pyro5
import threading
import logging
log = logging.getLogger()


@Pyro5.api.expose
class TMDemoWorkflow(mupif.Workflow):

    def __init__(self, metadata=None):
        MD = {
            "ClassName": "TMDemoWorkflow",
            "ModuleName": "tm_demo_workflow",
            "Name": "TM Demo Workflow",
            "ID": "tm_demo_workflow",
            "Description": "",
            "Execution_settings": {
                "Type": "Local"
            },
            "Inputs": [
                {"Name": "temperature_top", "Type": "mupif.Property", "Required": True, "description": "", "Type_ID": "mupif.DataID.PID_Temperature", "Obj_ID": "temperature_top", "Units": "deg_C", "Set_at": "timestep", "ValueType": "Scalar"},
                {"Name": "temperature_bottom", "Type": "mupif.Property", "Required": True, "description": "", "Type_ID": "mupif.DataID.PID_Temperature", "Obj_ID": "temperature_bottom", "Units": "deg_C", "Set_at": "timestep", "ValueType": "Scalar"}
            ],
            "Outputs": [
                {"Name": "field_temperature", "Type": "mupif.Field", "description": "", "Type_ID": "mupif.DataID.FID_Temperature", "Obj_ID": "field_temperature", "Units": "degC"},
                {"Name": "field_displacement", "Type": "mupif.Field", "description": "", "Type_ID": "mupif.DataID.FID_Displacement", "Obj_ID": "field_displacement", "Units": "m"},
                {"Name": "max_displacement", "Type": "mupif.Property", "description": "", "Type_ID": "mupif.DataID.PID_maxDisplacement", "Obj_ID": "max_displacement", "Units": "m", "ValueType": "Scalar"}
            ],
            "Models": [
                {
                    "Name": "model_1",
                    "Jobmanager": "OOFEM_Thermal_demo"
                },
                {
                    "Name": "model_2",
                    "Jobmanager": "MUPIF_Mechanical_demo"
                }
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.daemon = None

        # initialization code of external input (ext_slot_1)
        self.external_input_1 = None
        # It should be defined from outside using set() method.

        # initialization code of external input (ext_slot_2)
        self.external_input_2 = None
        # It should be defined from outside using set() method.

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

        ns = mupif.pyroutil.connectNameserver()
        self.daemon = mupif.pyroutil.getDaemon(ns)

    # set method for all external inputs
    def set(self, obj, objectID=''):

        # in case of mupif.PyroFile
        if obj.isInstance(mupif.PyroFile):
            pass

        # in case of mupif.Property
        if obj.isInstance(mupif.Property):
            pass
            if objectID == 'temperature_top':
                self.external_input_1 = obj
            if objectID == 'temperature_bottom':
                self.external_input_2 = obj

        # in case of mupif.Field
        if obj.isInstance(mupif.Field):
            pass

        # in case of mupif.HeavyStruct
        if obj.isInstance(mupif.HeavyStruct):
            pass

        # in case of mupif.String
        if obj.isInstance(mupif.String):
            pass

    # get method for all external outputs
    def get(self, objectTypeID, time=None, objectID=''):
        if objectID == 'field_temperature':
            return self.getModel('model_1').get(mupif.DataID.FID_Temperature, time, '')
        if objectID == 'field_displacement':
            return self.getModel('model_2').get(mupif.DataID.FID_Displacement, time, '')
        if objectID == 'max_displacement':
            return self.getModel('model_2').get(mupif.DataID.PID_maxDisplacement, time, 'max_displacement')

        return None

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        pass
        
        # execution code of model_1 (OOFEM demo API thermal)
        self.getModel('model_1').set(self.external_input_1, 'temperature_top')
        self.getModel('model_1').set(self.external_input_2, 'temperature_bottom')
        self.getModel('model_1').solveStep(tstep)
        
        # execution code of model_2 (MUPIF demo API mechanical)
        self.getModel('model_2').set(self.getModel('model_1').get(mupif.DataID.FID_Temperature, tstep.getTime(), ''), '')
        self.getModel('model_2').solveStep(tstep)


