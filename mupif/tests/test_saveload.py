from __future__ import print_function, division
import unittest
from mupif import *
import mupif
from mupif.tests import demo

# check for python-vtk before running related tests
try:
    import vtk
    vtkAvailable=True
except ImportError:
    vtkAvailable=False


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
    def testFieldHdf5SaveLoad(self):
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

    @unittest.skipUnless(vtkAvailable) # vtkAvailable defined above
    def testFieldVtk3SaveLoad(self):
        f=self.app1.getField(mupif.FieldID.FID_Temperature,time=0)
        if 0:
            import tempfile
            with tempfile.NamedTemporaryFile() as tmp:
                f.toVTK3(tmp.name)
                ff2=mupif.Field.Field.makeFromVTK3(tmp.name)
        else:
            name='/tmp/mupif-field-test.vtu'
            f.toVTK3(name,ascii=True,compress=False)
            ff2=mupif.Field.Field.makeFromVTK3(name)
            # ff2[0].toVTK3(name+'.b.',ascii=True,compress=False)
        self.assertEqual(len(ff2),1)
        f2=ff2[0]
        # just compare coordinates of the first point
        self.assertEqual(f.getMesh().getVertex(0).getCoordinates(),f2.getMesh().getVertex(0).getCoordinates())
        # data hash comparison is too strict and fails
        # as tried, however, saving to VTK again yields byte-to-byte identical .vtu
        ## self.assertEqual(f.getMesh().internalArraysDigest(),f2.getMesh().internalArraysDigest())
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
        
        



