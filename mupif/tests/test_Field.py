import unittest
import tempfile
from mupif import *
import mupif
import numpy as np
import numpy.testing


def mkVertex(number, label, coords): return vertex.Vertex(number=number, label=label, coords=coords)


try:
    import vtk
except ImportError:
    vtk = None

try:
    import pyvtk
except ImportError:
    pyvtk = None

try:
    import meshio
except ImportError:
    meshio = None


class Field_TestCase(unittest.TestCase):
    def setUp(self):

        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self.tmpdir.name
        # self.tmpdir,self.tmp=None,'/tmp/mupif'; os.makedirs(self.tmp,exist_ok=True) # for debugging

        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup([
            mkVertex(0, 0, (0., 0., 0.)),
            mkVertex(1, 1, (2., 0., 0.)),
            mkVertex(2, 2, (0., 5., 0.)),
            mkVertex(3, 3, (4., 2., 0.)),
            mkVertex(4, 4, (5., 4., 0.)),
            mkVertex(5, 5, (.5, 5.5, 0)),
        ], [
            cell.Triangle_2d_lin(mesh=self.mesh, number=1, label=1, vertices=(0, 1, 2)),
            cell.Triangle_2d_lin(mesh=self.mesh, number=2, label=2, vertices=(1, 2, 3)),
            cell.Quad_2d_lin(mesh=self.mesh, number=3, label=3, vertices=(2, 3, 4, 5))
        ])

        self.mesh3 = mesh.UnstructuredMesh()
        self.mesh3.setup([mkVertex(0, 16, (5., 6., 0.)), mkVertex(1, 5, (8., 8., 0.)), mkVertex(2, 8, (6., 10., 0.))], [cell.Triangle_2d_lin(mesh=self.mesh3, number=3, label=8, vertices=(0, 1, 2))])

        self.mesh4 = mesh.UnstructuredMesh()
        self.mesh4.setup([mkVertex(0, 0, (0., 0., 0.)), mkVertex(1, 1, (2., 0., 2.)), mkVertex(2, 2, (0., 5., 3.)), mkVertex(3, 3, (3., 3., 2.)), mkVertex(4, 4, (8., 15., 0.))], [cell.Tetrahedron_3d_lin(mesh=self.mesh4, number=1, label=1, vertices=(0, 1, 2, 3)), cell.Tetrahedron_3d_lin(mesh=self.mesh4, number=2, label=2, vertices=(1, 2, 3, 4))])

        self.f1 = field.Field(mesh=self.mesh, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=13*mupif.Q.s, quantity=[(0,), (12,), (175,), (94,), (100,), (101,)]*mupif.U.m, fieldType=FieldType.FT_vertexBased)
        self.f2 = field.Field(mesh=self.mesh, fieldID=DataID.FID_Strain, valueType=ValueType.Vector, time=128*mupif.Q.s, quantity=[(3, 6), (2, 8), (2, 3)]*mupif.U['kg/(m*s**2)'], fieldType=FieldType.FT_vertexBased)

        self.f3 = field.Field(mesh=self.mesh, fieldID=DataID.FID_Stress, valueType=ValueType.Tensor, time=66*mupif.Q.s, quantity=[(3, 6, 4), (2, 8, 5), (2, 3, 6)]*mupif.U['kg/(m*s**2)'], fieldType=FieldType.FT_vertexBased)

        self.f4 = field.Field(mesh=self.mesh4, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=16*mupif.Q.s, quantity=[(6,), (16,), (36,), (33,), (32,)]*mupif.U.m, fieldType=FieldType.FT_vertexBased)
        self.f5 = field.Field(mesh=self.mesh3, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=13*mupif.Q.s, quantity=[(3,), (5,), (4,)]*mupif.U.m, fieldType=FieldType.FT_vertexBased)
        self.f6 = field.Field(mesh=self.mesh4, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=16*mupif.Q.s, quantity=[(0,), (12,), (39,), (33,), (114,)]*mupif.U.m, fieldType=FieldType.FT_vertexBased)
        self.f7 = field.Field(mesh=self.mesh4, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=16*mupif.Q.s, quantity=[(2,), (16,)]*mupif.U.m, fieldType=FieldType.FT_cellBased)
        self.f8 = field.Field(mesh=self.mesh, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar,
                              time=13*mupif.Q.s, quantity=[]*mupif.U.m, fieldType=FieldType.FT_vertexBased)
        self.f9 = field.Field(mesh=self.mesh, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar,
                              time=13*mupif.Q.s, quantity=[]*mupif.U.m,
                              fieldType=FieldType.FT_cellBased)

        l = len(self.f8.value)
        self.assertEqual(l, self.mesh.getNumberOfVertices())
        l = len(self.f9.value)
        self.assertEqual(l, self.mesh.getNumberOfCells())

    def tearDown(self):
        if self.tmpdir:
            self.tmpdir.cleanup()
        
    # unit tests support
    # def assertphysicalquantitiesEqual(self, first, second, msg=None):
    #     if not first.__cmp__(second):
    #         raise self.failureException(msg)

    def test_getRecordSize(self):
        self.assertEqual(self.f1.getRecordSize(), 1)
        self.assertEqual(self.f2.getRecordSize(), 3)
        self.assertEqual(self.f3.getRecordSize(), 9)
        self.assertEqual(self.f4.getRecordSize(), 1)
                
    def test_getMesh(self):
        from rich.pretty import pprint
        pprint(self.f1.getMesh())
        pprint(self.mesh)
        self.assertEqual(hex(id(self.f1.getMesh())), hex(id(self.mesh)))
        self.assertEqual(hex(id(self.f4.getMesh())), hex(id(self.mesh4)))
        
    def test_getValueType(self):
        self.assertEqual(self.f1.getValueType(), ValueType.Scalar)
        self.assertEqual(self.f2.getValueType(), ValueType.Vector)
        self.assertEqual(self.f3.getValueType(), ValueType.Tensor)
        self.assertEqual(self.f4.getValueType(), ValueType.Scalar)
        
    def test_getFieldID(self):
        self.assertEqual(self.f1.getFieldID(), DataID.FID_Displacement)
        self.assertEqual(self.f2.getFieldID(), DataID.FID_Strain)
        self.assertEqual(self.f3.getFieldID(), DataID.FID_Stress)
        self.assertEqual(self.f4.getFieldID(), DataID.FID_Displacement)
        
    def test_getFieldIDName(self):
        self.assertEqual(self.f1.getFieldIDName(), 'FID_Displacement')
        self.assertEqual(self.f2.getFieldIDName(), 'FID_Strain')
        self.assertEqual(self.f3.getFieldIDName(), 'FID_Stress')
        self.assertEqual(self.f4.getFieldIDName(), 'FID_Displacement')
        
    def test_getFieldType(self):
        self.assertEqual(self.f1.getFieldType(), field.FieldType.FT_vertexBased)
        self.assertEqual(self.f7.getFieldType(), field.FieldType.FT_cellBased)
                
    def test_getTime(self):
        self.assertEqual(self.f1.getTime().getValue(), 13)
        self.assertEqual(self.f2.getTime().getValue(), 128)
        self.assertEqual(self.f3.getTime().getValue(), 66)
        self.assertEqual(self.f4.getTime().getValue(), 16)
        
    def test_evaluate(self):
        np.testing.assert_array_equal(self.f1.evaluate((1., 2.5, 0.)).getValue(), (93.5,))
        np.testing.assert_array_equal(self.f1.evaluate((3., 1., 0.)).getValue(), (53.,))
        np.testing.assert_array_equal(self.f6.evaluate((2., 2., 2.)).getValue(), (24.,))
        np.testing.assert_array_equal(self.f6.evaluate((1.5, 1.5, 1.5)).getValue(), (18.,))

        import astropy.units as au
        self.assertRaises(RuntimeError, lambda: self.f1.evaluate((1., 2.5, 0)*au.m))
        self.f1.getMesh().unit = au.m
        np.testing.assert_array_equal(self.f1.evaluate((1., 2.5, 0.)*au.m).getValue(), (93.5,))
        np.testing.assert_array_equal(self.f1.evaluate((1000, 2500, 0)*au.mm).getValue(), (93.5,))
        self.assertRaises(au.UnitConversionError, lambda: self.f1.evaluate((1, 2, 3)*au.s))

    def test_getVertexValue(self):
        self.assertEqual(self.f1.getVertexValue(0).getValue(), (0,))
        self.assertEqual(self.f1.getVertexValue(1).getValue(), (12,))
        self.assertEqual(self.f1.getVertexValue(2).getValue(), (175,))
        self.assertEqual(self.f4.getVertexValue(0).getValue(), (6,))
        self.assertEqual(self.f4.getVertexValue(1).getValue(), (16,))
        self.assertEqual(self.f4.getVertexValue(2).getValue(), (36,))
        self.assertEqual(self.f4.getVertexValue(3).getValue(), (33,))

    def test_setRecord(self):
        self.f1.setRecord(0, [5])
        self.assertEqual(self.f1.getVertexValue(0).getValue(), (5,))
        
        self.f4.setRecord(3, [5])
        self.assertEqual(self.f4.getVertexValue(3).getValue(), (5,))

    def test_getUnit(self):
        self.assertEqual(self.f1.getUnit(), mupif.U.m)
        self.assertEqual(self.f2.getUnit(), mupif.U['kg/(m*s**2)'])
        
    def test_merge(self):
        self.f5.merge(self.f1)
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[0].label, 16)
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[1].label, 5)
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[2].label, 8)
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[0].label, 0)
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[1].label, 1)
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[2].label, 2)
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[0].label, 1)
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[1].label, 2)
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[2].label, 3)

    def _compareFields(self, orig, loaded, units=True):
        self.assertEqual(orig.getRecordSize(), loaded.getRecordSize())
        self.assertEqual(orig.getValueType(), loaded.getValueType())
        self.assertEqual(orig.getFieldID(), loaded.getFieldID())
        self.assertEqual(orig.getFieldIDName(), loaded.getFieldIDName())
        self.assertEqual(orig.getTime().getValue(), loaded.getTime().getValue())
        self.assertEqual(orig.getVertexValue(0), loaded.getVertexValue(0))
        self.assertEqual(orig.getVertexValue(1), loaded.getVertexValue(1))
        self.assertEqual(orig.getVertexValue(2), loaded.getVertexValue(2))
        self.assertEqual(orig.getVertexValue(3), loaded.getVertexValue(3))
        self.assertEqual(orig.getUnit().name, loaded.getUnit().name)
        
    def test_ioDump(self):
        f = self.tmp+'/aa.dump'
        self.f1.dumpToLocalFile(f)
        res = self.f1.loadFromLocalFile(f)
        self._compareFields(self.f1, res)

    def test_ioHdf5(self):
        f = self.tmp+'/aa.hdf5'
        self.f1.toHdf5(fileName=f)
        res = self.f1.makeFromHdf5(fileName=f)[0]
        self._compareFields(self.f1, res)

    @unittest.skipIf(meshio is None, 'meshio not importable')
    def test_ioMeshio(self):
        m = self.f1.toMeshioMesh()
        for ext in 'vtu', 'vtk', 'xdmf':
            out = self.tmp+'/meshio.'+ext
            # out = '/tmp/meshio.'+ext
            m.write(out)
            res = field.Field.makeFromMeshioMesh(out, unit={self.f1.getFieldIDName(): self.f1.getUnit()}, time=self.f1.getTime())[0]
            self._compareFields(self.f1, res)


# python test_Field.py for stand-alone test being run
if __name__ == '__main__':
    unittest.main()
