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
import Pyro5

class TemporalField_TestCase(unittest.TestCase):
    #@classmethod
    #def setUpClass(cls):
    #    cls.daemon=mp.pyroutil.getDaemon()
    def test_01_ctor(self):
        mo=mp.MupifObject()
        m1=mp.MupifQuantity(1,'m')
        mol=MOL([mo,mo])
        self.assertTrue(mol.typeId,'mupif.mupifobject.MupifObject')
        mol=MOL(objs=[m1,m1])
        self.assertTrue(mol.typeId,'mupif.mupifobject.MupifQuantity')
        self.assertRaises(pydantic.ValidationError,lambda: MOL([mo,m1]))
        self.assertRaises(pydantic.ValidationError,lambda: MOL(objs=[mo,m1]))
        self.assertRaises(ValueError,lambda: MOL(1.44))
        self.assertRaises(ValueError,lambda: MOL([mo],objs=[mo]))
    #def test_02_pyro(self):
    #    C=self.__class__
    #    m1=MOL([mp.MupifQuantity(1,'m'),mp.MupifQuantity(2,'m')])
    #    uri=C.daemon.register(m1)
    #    m1p=Pyro5.api.Proxy(uri)
    #    self.assertEqual(m1p.typId
    #    self.assertEqual(len(m1p.objs),2)
    #    self.assertEqual(m1p.quantity,1)
    #    self.assertEqual(m1p.unit,'m')


    # instantiating objects
    # pyro transfer
        


if __name__=='__main__':
    pytest.main([__file__])

