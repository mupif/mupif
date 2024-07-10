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




