import unittest
import os
import tempfile
import mupif as mp

try: import vtk
except ImportError: vtk=None

thisDir=os.path.dirname(os.path.abspath(__file__))

if 0:
    # this is how data/test_field.structured_points.vtk was produced
    import pyvista as pv
    import numpy as np
    pv.set_jupyter_backend('trame')
    gr=pv.UniformGrid(dimensions=(5,7,11),spacing=(.5,.7,1.1),origin=(5,7,11))
    dSca=np.zeros(gr.dimensions,order='F')
    dVec=np.zeros(list(gr.dimensions)+[3],order='F')
    dSca[:,:,::3]=1
    dSca[:,::2,:]=2
    dSca[0,:,:]=0
    dVec[:,:,:]=(5,7,11)
    gr.point_data['dScalar']=dSca.T.ravel()
    gr.point_data['dVector']=dVec.reshape(dVec.shape[-1],-1).T
    gr.save('data/test_field.structured_points.vtk')


class TestFieldHdf5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
    @classmethod
    def tearDownClass(cls):
        try: cls.tmpdir.cleanup()
        except: pass

    @unittest.skipIf(vtk is None,'vtk not importable')
    def test_load_save_load(self):
        C=self.__class__
        def test_values_f0(f):
            def aae(xyz,exp): self.assertAlmostEqual(f.evaluate(xyz,eps=1e-4).value[0],exp,places=5)
            aae((7.0,7.7,12.1),0)
            aae((5.0,7.7,13.2),0)
            aae((6.0,8.4,22.0),2)
            aae((7.0,7.7,14.3),1)
        ff=mp.Field.makeFromVtkFile(
            thisDir+'/data/test_field_hdf5.structured_points.vtk',
            fieldIDs={'dScalar':mp.DataID.FID_Pressure,'dVector':mp.DataID.FID_Displacement}
        )
        for i in range(100):
            print(i,ff[0].mesh.i2ijk(i))
        test_values_f0(ff[0])
        for f in ff: f.toHdf5(fileName=C.tmp+'/bb.h5',groupName='/')
        ff2=mp.Field.makeFromHdf5(fileName=C.tmp+'/bb.h5',group='/',indices=None,heavy=True,h5own=True)
        test_values_f0(ff2[0])
        ff2[0].mesh.writeXDMF(fields=ff2)
