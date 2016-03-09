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
        import mupif.Field
        f=self.app1.getField(mupif.FieldID.FID_Temperature,time=0)
        if 1: # when testing locally, set to 0 so that the dump file can be inspected
            import tempfile
            with tempfile.NamedTemporaryFile() as tmp:
                f.toHdf5(tmp.name)
                ff2=mupif.Field.Field.makeFromHdf5(tmp.name)
        else:
            name='/tmp/mupif-field-test.hdf5'
            f.toHdf5(name)
            ff2=mupif.Field.Field.makeFromHdf5(name)
        self.assertEqual(len(ff2),1)
        f2=ff2[0]
        self.assertEqual(f.getMesh().internalArraysDigest(),f2.getMesh().internalArraysDigest())
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
        
        



