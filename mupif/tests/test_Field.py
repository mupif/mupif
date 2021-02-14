import unittest
import tempfile
from mupif import *
from mupif.physics.physicalquantities import PhysicalUnit as PU
import mupif.physics.physicalquantities as PQ
import math, os
import numpy as np

try: import vtk
except ImportError: vtk=None

try: import pyvtk
except ImportError: pyvtk=None

try: import meshio
except ImportError: meshio=None

class Field_TestCase(unittest.TestCase):
    def setUp(self):

        self.tmpdir=tempfile.TemporaryDirectory()
        self.tmp=self.tmpdir.name
        # self.tmpdir,self.tmp=None,'/tmp/mupif'; os.makedirs(self.tmp,exist_ok=True) # for debugging
        
        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup([vertex.Vertex(0,0,(0.,0.,0.)), vertex.Vertex(1,1,(2.,0.,0.)), vertex.Vertex(2,2,(0.,5.,0.)), vertex.Vertex(3,3,(4.,2.,0.))], [cell.Triangle_2d_lin(self.mesh,1,1,(0,1,2)),cell.Triangle_2d_lin(self.mesh,2,2,(1,2,3))])

        self.mesh3 = mesh.UnstructuredMesh()
        self.mesh3.setup([vertex.Vertex(0,16,(5.,6.,0.)), vertex.Vertex(1,5,(8.,8.,0.)), vertex.Vertex(2,8,(6.,10.,0.))], [cell.Triangle_2d_lin(self.mesh3,3,8,(0,1,2))])
        
        self.mesh4 = mesh.UnstructuredMesh()
        self.mesh4.setup([vertex.Vertex(0,0,(0.,0.,0.)), vertex.Vertex(1,1,(2.,0.,2.)), vertex.Vertex(2,2,(0.,5.,3.)),vertex.Vertex(3,3,(3.,3.,2.)),vertex.Vertex(4,4,(8.,15.,0.))], [cell.Tetrahedron_3d_lin(self.mesh4,1,1,(0,1,2,3)),cell.Tetrahedron_3d_lin(self.mesh4,2,2,(1,2,3,4))])
        
        
        self.f1=field.Field(self.mesh,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(13, 's'),[(0,),(12,),(175,),(94,)],1)
        self.f2=field.Field(self.mesh,FieldID.FID_Strain,ValueType.Vector,PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),PQ.PhysicalQuantity(128,'s'),[(3,6),(2,8),(2,3)],1)
        self.f3=field.Field(self.mesh,FieldID.FID_Stress,ValueType.Tensor,PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),PQ.PhysicalQuantity(66,'s'),[(3,6,4),(2,8,5),(2,3,6)],1)
        self.f4=field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(6,),(16,),(36,),(33,),(32,)])
        self.f5=field.Field(self.mesh3,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(13,'s'),[(3,),(5,),(4,)],1)
        self.f6=field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(0,),(12,),(39,),(33,),(114,)])
        self.f7=field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(2,),(16,)],field.FieldType.FT_cellBased)
        self.f8 = field.Field(self.mesh, FieldID.FID_Displacement, ValueType.Scalar,
                              PU({'m': 1}, 1, (1, 0, 0, 0, 0, 0, 0)), PQ.PhysicalQuantity(13, 's'), None, 1)
        self.f9 = field.Field(self.mesh, FieldID.FID_Displacement, ValueType.Scalar,
                              PU({'m': 1}, 1, (1, 0, 0, 0, 0, 0, 0)), PQ.PhysicalQuantity(13, 's'), None,
                              field.FieldType.FT_cellBased)

        l = len(self.f8.value)
        self.assertEqual(l, self.mesh.getNumberOfVertices())
        l = len(self.f9.value)
        self.assertEqual(l, self.mesh.getNumberOfCells())


        # register assertEqual operation for physicalquantities
        self.addTypeEqualityFunc(PQ.PhysicalQuantity, self.assertphysicalquantitiesEqual)
        
    def tearDown(self):

        if self.tmpdir: self.tmpdir.cleanup()
        
        self.f1 = None
        self.f2 = None
        self.f3 = None
        self.f4 = None
        self.f5 = None
        self.f6 = None
        self.mesh = None
        self.mesh3 = None
        self.mesh5 = None

    # unit tests support
    def assertphysicalquantitiesEqual(self, first, second, msg=None):
        if not first.__cmp__(second):
            raise self.failureException(msg)

    def test_getRecordSize(self):
        self.assertEqual(self.f1.getRecordSize(), 1, 'error in getRecordSize for f1')
        self.assertEqual(self.f2.getRecordSize(), 3, 'error in getRecordSize for f2')
        self.assertEqual(self.f3.getRecordSize(), 9, 'error in getRecordSize for f3')
        self.assertEqual(self.f4.getRecordSize(), 1, 'error in getRecordSize for f4')   
                
    def test_getMesh(self):
        self.assertEqual(self.f1.getMesh(),self.mesh, 'error in getMesh for f1')
        self.assertEqual(self.f4.getMesh(),self.mesh4, 'error in getMesh for f4')
        
    def test_getValueType(self):
        self.assertEqual(self.f1.getValueType(),ValueType.Scalar, 'error in getValueType for f1')
        self.assertEqual(self.f2.getValueType(),ValueType.Vector, 'error in getValueType for f2')
        self.assertEqual(self.f3.getValueType(),ValueType.Tensor, 'error in getValueType for f3')
        self.assertEqual(self.f4.getValueType(),ValueType.Scalar, 'error in getValueType for f4')
        
    def test_getFieldID(self):
        self.assertEqual(self.f1.getFieldID(),FieldID.FID_Displacement,'error in getFieldID for f1')
        self.assertEqual(self.f2.getFieldID(),FieldID.FID_Strain,'error in getFieldID for f2')
        self.assertEqual(self.f3.getFieldID(),FieldID.FID_Stress,'error in getFieldID for f3')
        self.assertEqual(self.f4.getFieldID(),FieldID.FID_Displacement,'error in getFieldID for f4')
        
    def test_getFieldIDName(self):
        self.assertEqual(self.f1.getFieldIDName(),'FID_Displacement','error in getFieldIDName for f1')
        self.assertEqual(self.f2.getFieldIDName(),'FID_Strain','error in getFieldIDName for f2')
        self.assertEqual(self.f3.getFieldIDName(),'FID_Stress','error in getFieldIDName for f3')
        self.assertEqual(self.f4.getFieldIDName(),'FID_Displacement','error in getFieldIDName for f4')
        
    def test_getFieldType(self):
        self.assertEqual(self.f1.getFieldType(),field.FieldType.FT_vertexBased,'error in FieldType for f1')
        self.assertEqual(self.f7.getFieldType(),field.FieldType.FT_cellBased,'error in FieldType for f4')
                
    def test_getTime(self):
        self.assertEqual(self.f1.getTime().getValue(),13, 'error in getTime for f1') 
        self.assertEqual(self.f2.getTime().getValue(),128, 'error in getTime for f2')
        self.assertEqual(self.f3.getTime().getValue(),66, 'error in getTime for f3')
        self.assertEqual(self.f4.getTime().getValue(),16, 'error in getTime for f4')
        
    def test_evaluate(self):
        self.assertEqual(self.f1.evaluate((1.,2.5,0.)).getValue(),(93.5,),'error in evaluate for f1(point 1.,2.5,0.)')
        self.assertEqual(self.f1.evaluate((3.,1.,0.)).getValue(),(53.,),'error in evaluate for f1(point 3.,1.,0.)')
        self.assertEqual(self.f6.evaluate((2.,2.,2.)).getValue(),(24.,),'error in evaluate for f1(point 2.,2.,2.)')
        self.assertEqual(self.f6.evaluate((1.5,1.5,1.5)).getValue(),(18.,),'error in evaluate for f1(point 2.,2.,2.)')

    def test_getVertexValue(self):
        self.assertEqual(self.f1.getVertexValue(0).getValue(),(0,),'error in getVertexValuep for f1')
        self.assertEqual(self.f1.getVertexValue(1).getValue(),(12,),'error in getVertexValue for f1')
        self.assertEqual(self.f1.getVertexValue(2).getValue(),(175,),'error in getVertexValue for f1')
        self.assertEqual(self.f4.getVertexValue(0).getValue(),(6,),'error in getVertexValue for f4')
        self.assertEqual(self.f4.getVertexValue(1).getValue(),(16,),'error in getVertexValue for f4')
        self.assertEqual(self.f4.getVertexValue(2).getValue(),(36,),'error in getVertexValue for f4')
        self.assertEqual(self.f4.getVertexValue(3).getValue(),(33,),'error in getVertexValue for f4')
    def test_setValue(self):
        self.f1.setValue(0,[5])
        self.f1.commit()
        self.assertEqual(self.f1.getVertexValue(0).getValue(),[5],'error in setValue for f1') 
        
        self.f4.setValue(3,[5])
        self.f4.commit()
        self.assertEqual(self.f4.getVertexValue(3).getValue(),[5],'error in setValue for f4')
    def test_getUnits(self):
        self.assertEqual(self.f1.getUnits(),PU({'m': 1}, 1,(1,0,0,0,0,0,0)),'error in getUnits for f1')
        self.assertEqual(self.f2.getUnits(),PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),'error in getUnits for f2')
        
    def test_merge(self):
        self.f5.merge(self.f1)
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[0].label,16,'error in merge (label 16)')
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[1].label,5,'error in merge (label 5)')
        self.assertEqual(self.f5.getMesh().getCell(0).getVertices()[2].label,8,'error in merge (label 8)')
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[0].label,0,'error in merge (label 0)')
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[1].label,1,'error in merge (label 1)')
        self.assertEqual(self.f5.getMesh().getCell(1).getVertices()[2].label,2,'error in merge (label 2)')
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[0].label,1,'error in merge (label 1)')
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[1].label,2,'error in merge (label 2)')
        self.assertEqual(self.f5.getMesh().getCell(2).getVertices()[2].label,3,'error in merge (label 3)')

    def _compareFields(self,orig,loaded,units=True):
        self.assertEqual(orig.getRecordSize(),loaded.getRecordSize())
        self.assertEqual(orig.getValueType(),loaded.getValueType())
        self.assertEqual(orig.getFieldID(),loaded.getFieldID())
        self.assertEqual(orig.getFieldIDName(),loaded.getFieldIDName())
        self.assertEqual(orig.getTime().getValue(),loaded.getTime().getValue())
        self.assertEqual(orig.getVertexValue(0),loaded.getVertexValue(0))
        self.assertEqual(orig.getVertexValue(1),loaded.getVertexValue(1))
        self.assertEqual(orig.getVertexValue(2),loaded.getVertexValue(2))
        self.assertEqual(orig.getVertexValue(3),loaded.getVertexValue(3))
        self.assertEqual(orig.getUnits().name(),loaded.getUnits().name())
        
    def test_ioDump(self):
        f=self.tmp+'/aa.dump'
        self.f1.dumpToLocalFile(f)
        res=self.f1.loadFromLocalFile(f)
        self._compareFields(self.f1,res)

    def test_ioHdf5(self):
        f=self.tmp+'/aa.hdf5'
        self.f1.toHdf5(f)
        res=self.f1.makeFromHdf5(f)[0]
        self._compareFields(self.f1,res)

    @unittest.skipIf(pyvtk is None,'pyvtk not importable')
    def test_field2VTKData(self):
       self.res=self.f5.field2VTKData()
       import pyvtk
       self.assertTrue(isinstance(self.res,pyvtk.VtkData),'error in getVTKRepresentation')

    @unittest.skipIf(pyvtk is None,'pyvtk not importable')
    def test_ioVTK2(self):
        f=self.tmp+'/aa.vtk'
        self.f1.toVTK2(f)
        res=self.f1.makeFromVTK2(f, PU({'m': 1}, 1,(1,0,0,0,0,0,0)), time=self.f1.getTime())[0]
        # VTK2 does not store units
        self._compareFields(self.f1,res,units=False)
       
    @unittest.skipIf(vtk is None,'vtk (python-vtk*) not importable')
    def test_ioVTK3(self):
        f=self.tmp+'/aa.vtu'
        self.f1.toVTK3(f)
        self.res=self.f1.makeFromVTK3(f,units=self.f1.getUnits(),time=self.f1.getTime())[0]
        self._compareFields(self.f1,self.res)

    @unittest.skipIf(meshio is None,'meshio not importable')
    def test_ioMeshio(self):
        m=self.f1.toMeshioMesh()
        for ext in 'vtu','vtk','xdmf':
            out=self.tmp+'/meshio.'+ext
            m.write(out)
            res=field.Field.makeFromMeshioMesh(out,units={self.f1.getFieldIDName():self.f1.getUnits()},time=self.f1.getTime())[0]
            self._compareFields(self.f1,res)


# python test_Field.py for stand-alone test being run
if __name__=='__main__': unittest.main()
