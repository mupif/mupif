import unittest,sys
sys.path.append('../..')
from mupif import *
import jsonschema








class testModel1(model.Model):
    """ Empty model1(with missing required metadata) to test metadata setting"""

    def __init__(self, metaData={}):
        metaData1 = {
            'Name': 'Empty application to test metadata',
            'ID': 'N/A',
            'Description': 'Model with missing metadata',
        }
        
        super(testModel1, self).__init__(metaData1)
        self.updateMetadata(metaData)
        
       
    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        super(testModel1, self).initialize(metaData=metaData, validateMetaData=validateMetaData, **kwargs)



class testModel2(model.Model):
    """ Empty model2 to test metadata setting"""

    def __init__(self, metaData={}):
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step', 'Units': 's', 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super(testModel2, self).__init__(metaData=MD)
        self.updateMetadata(metaData)

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        super(testModel2, self).initialize(file, workdir, metaData, validateMetaData, **kwargs)

        
    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == PropertyID.PID_Time_step:
            return property.ConstantProperty(time, PropertyID.PID_Time_step, ValueType.Scalar, 's', metaData=md)

    
    


        

class Metadata_TestCase(unittest.TestCase):
    def setUp(self):
        self.tm1 = testModel1()
        self.tm2 = testModel2()

    def test_Init(self):
        try:
            self.tm1.initialize()
        except jsonschema.exceptions.ValidationError: pass
        #except fastjsonschema.JsonSchemaException: pass
        except Exception as e:
            self.fail('Unexpected exception raised: %s'%e)
        else:
            self.fail('Exception not raised')



        executionMetadata = {
            'Execution': {
                'ID': '1',
                'Use_case_ID': '1_1',
                'Task_ID': '1'
            }
        }
        try:            
            self.tm2.initialize(metaData = executionMetadata)
        except Exception as e:
            self.fail('Unexpected exception raised:', e)

            
    def test_Name(self):
        name = self.tm2.getMetadata('Name')
        if name ==  'Empty application to test metadata':
            pass
        else:
            self.fail('wrong name')

    def test_SolverLanguage(self):
        lang = self.tm2.getMetadata('Solver.Language')
        if lang ==  'Python3':
            pass
        else:
            self.fail('wrong language')


    def test_propery(self):
        executionMetadata = {
            'Execution': {
                'ID': '1',
                'Use_case_ID': '1_1',
                'Task_ID': '1'
            }
        }
        try:            
            self.tm2.initialize(metaData = executionMetadata)
        except Exception as e:
            self.fail('Unexpected exception raised: %s'%e)
        propeucid = self.tm2.getProperty(PropertyID.PID_Time_step, timestep.TimeStep(1., 1., 10, 's')).getMetadata('Execution.Use_case_ID')
        if propeucid == self.tm2.getMetadata('Execution.Use_case_ID'):
            pass
        else:
            self.fail('wrong propery exectuion use case ID')
            

        
# python test_Metadata.py for stand-alone test being run
if __name__=='__main__': unittest.main()

        
        
    
        
