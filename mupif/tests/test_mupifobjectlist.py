import unittest
import pytest
import tempfile
import mupif as mp
from mupif import MupifObjectList as MOL
import mupif as mp
import math, os, os.path
import numpy as np
import astropy.units as au
import pydantic

class TemporalField_TestCase(unittest.TestCase):
    def test_01_ctor(self):
        mo=mp.MupifObject()
        m1=mp.MupifQuantity(1,'m')
        mol=MOL([mo,mo])
        self.assertTrue(mol.typeId,'mupif.mupifobject.MupifObject')
        mol=MOL([m1,m1])
        self.assertTrue(mol.typeId,'mupif.mupifobject.MupifQuantity')
        self.assertRaises(pydantic.ValidationError,lambda: MOL([mo,m1]))

        


if __name__=='__main__':
    pytest.main([__file__])

