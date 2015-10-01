from __future__ import print_function, division
import unittest
from mupif import *
import mupif
from mupif.tests import demo


class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.app1=demo.AppGridAvg(None)
    def testFieldSaveLoad(self):
        # get field from the app
        f=self.app1.getField(mupif.FieldID.FID_Temperature,time=0)
        print(f.mesh)
        t22a=f.evaluate((2.0,2.0,0.)) # temperature at (2,2)
        import pickle
        p=pickle.dumps(f)
        f2=pickle.loads(p)
        t22b=f.evaluate((2.,2.,0.))
        self.assert_(not id(f)==id(f2))
        self.assertEqual(t22a,t22b)


