import unittest
import sys
sys.path.append('../..')
from mupif import *
import mupif
import jsonschema
import pydantic

# undescored so that pytest does not see it as a test case
class _TestModel1(model.Model):
    """ Empty model1(with missing required metadata) to test metadata setting"""

    def __init__(self, metadata=None):
        metadata1 = {
            'Name': 'Empty application to test metadata',
            'ID': 'N/A',
            'Description': 'Model with missing metadata',
        }
        super().__init__(metadata=metadata1)
        self.updateMetadata(metadata)

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(metadata=metadata, validateMetaData=validateMetaData, **kwargs)


class _TestModel2(model.Model):
    """ Empty model2 to test metadata setting"""

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Empty application to test metadata',
            'ID': 'N/A',
            'Description': 'Model with all metadata',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Python script',
                'Language': 'Python3',
                'License': 'LGPL',
                'Creator': 'nitram',
                'Version_date': '03/2019',
                'Type': 'Summator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'High',
                'Sensitivity': 'High',
                'Complexity': 'Low',
                'Robustness': 'High'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep", "ValueType": "Scalar"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time_step', 'Name': 'Time step', 'Units': 's', 'Origin': 'Simulated', "ValueType": "Scalar"}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=""):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        if objectTypeID == DataID.PID_Time_step:
            return property.ConstantProperty(value=time.inUnitsOf(mupif.U.s).getValue(), propID=DataID.PID_Time_step, valueType=ValueType.Scalar, unit=mupif.U.none, time=time, metadata=md)


class Metadata_TestCase(unittest.TestCase):
    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    def setUp(self):
        self.tm1 = _TestModel1()
        self.tm2 = _TestModel2()

    def test_Init(self):
        with self.assertRaises(pydantic.ValidationError):
            # this fails because ID must not be None
            self.tm1.initialize(metadata={'ID':None})
        self.tm2.initialize(metadata=Metadata_TestCase.executionMetadata)

    def test_Name(self):
        self.assertEqual(self.tm2.getMetadata('Name'), 'Empty application to test metadata')

    def test_SolverLanguage(self):
        self.assertEqual(self.tm2.getMetadata('Solver.Language'), 'Python3')

    def test_property(self):
        self.tm2.initialize(metadata=Metadata_TestCase.executionMetadata)
        import pprint
        pprint.pprint(self.tm2.metadata)
        propeucid = self.tm2.get(objectTypeID=DataID.PID_Time_step, time=1.*mupif.U.s).getMetadata('Execution.Use_case_ID')
        self.assertEqual(propeucid, self.tm2.getMetadata('Execution.Use_case_ID'))


# python test_Metadata.py for stand-alone test being run
if __name__ == '__main__':
    unittest.main()
