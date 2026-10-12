import unittest
import tempfile
from mupif import *
import mupif as mp
import pytest
import pydantic
import typing

class Meta_TestCase(unittest.TestCase):
    def test_iometa(self):
        # mupif.Property must have ValueType
        pOk =dict(Type='mupif.Property',Type_ID='FID_Temperature',Name='whatever',ValueType='Scalar',Units='K')
        pErr=dict(Type='mupif.Property',Type_ID='FID_Temperature',Name='whatever',ValueType='',Units='K')
        ppOk =dict(Type='mupif.DataList[mupif.Property]',Type_ID='FID_Temperature',Name='whatever',ValueType='Scalar',Units='K')
        ppErr=dict(Type='mupif.DataList[mupif.Property]',Type_ID='FID_Temperature',Name='whatever',ValueType='',Units='K')
        # no restrictions on string or others
        sOk=dict(Type='mupif.String',Type_ID='FID_Temperature',Name='whatever',ValueType='Scalar',Units='K')
        with self.assertRaises(pydantic.ValidationError):
            mp.meta.IOMeta(**pErr)
            mp.meta.IOMeta(**ppErr)
        mp.meta.IOMeta(**pOk)
        mp.meta.IOMeta(**ppOk)
        mp.meta.IOMeta(**sOk)

    def test_mergedDicts_is_recursive(self):
        """Updating one nested field keeps the other fields of the nested dictionary; other values are replaced."""
        a={'Name':'x','Execution':{'ID':'E1','Log_URI':'PYRO:obj_log@host:1','Status':'Instantiated'},'Tags':[1,2]}
        merged=mp.meta._mergedDicts(a,{'Execution':{'Status':'Initialized'},'Tags':[3]})
        self.assertEqual(merged,{'Name':'x','Execution':{'ID':'E1','Log_URI':'PYRO:obj_log@host:1','Status':'Initialized'},'Tags':[3]})
        self.assertEqual(a['Execution']['Status'],'Instantiated')  # arguments not modified

    def test_initialize_keeps_execution_metadata(self):
        """
        Model.initialize() keeps the Execution metadata given by the caller.

        It used to drop it: the status update it makes replaced the whole Execution dictionary, so a
        workflow lost e.g. the Log_URI of the execution script and its models logged elsewhere.
        """
        class M(mp.Model):
            def __init__(self):
                super().__init__(metadata={'Name':'m','ID':'m','Description':'d','Physics':{'Type':'Other','Entity':'Other'},
                    'Solver':{'Software':'s','Language':'Python','License':'LGPL','Creator':'c','Version_date':'1','Type':'Summator','Documentation':'d','Estim_time_step_s':1,'Estim_comp_time_s':1,'Estim_execution_cost_EUR':0,'Estim_personnel_cost_EUR':0,'Required_expertise':'None','Accuracy':'Low','Sensitivity':'Low','Complexity':'Low','Robustness':'Low'},
                    'Inputs':[],'Outputs':[]})
            def getApplicationSignature(self): return 'M'
        m=M()
        m.initialize(metadata={'Execution':{'ID':'E1','Use_case_ID':'uc','Task_ID':'t','Log_URI':'PYRO:obj_log@host:1'}},validateMetaData=False)
        self.assertEqual((m.getMetadata('Execution.ID'),m.getMetadata('Execution.Log_URI'),m.getMetadata('Execution.Status')),('E1','PYRO:obj_log@host:1','Initialized'))
