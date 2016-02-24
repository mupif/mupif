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
        t22a=f.evaluate((2.0,2.0,0.)) # temperature at (2,2)
        import pickle
        p=pickle.dumps(f)
        f2=pickle.loads(p)
        t22b=f.evaluate((2.,2.,0.))
        self.assert_(not id(f)==id(f2))
        self.assertEqual(t22a,t22b)
    def testFieldHdf5Save(self):
        f=self.app1.getField(mupif.FieldID.FID_Temperature,time=0)
        if 1: # when testing locally, set to 0 so that the dump file can be inspected
            from tempdir import TempDir
            with TempDir() as d:
                f.toHdf5(d+'/field.hdf5')
        else:
            f.toHdf5('/tmp/mupif-field-test.hdf5')
    def testOctreeNotPickled(self):
        f=self.app1.getField(mupif.FieldID.FID_Temperature,time=0)
        import pickle
        m=f.getMesh()
        # this creates localizers on-request
        m.giveVertexLocalizer()
        m.giveCellLocalizer()
        # check localizers are there (break encapsulation, sorry)
        self.assert_(m.vertexOctree is not None)
        self.assert_(m.cellOctree is not None)
        p=pickle.dumps(m)
        # but that they were not pickled
        m2=pickle.loads(p)
        self.assert_(m2.vertexOctree is None)
        self.assert_(m2.cellOctree is None)
        
        


