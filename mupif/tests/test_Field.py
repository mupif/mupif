import unittest
import tempfile
from mupif import *
from mupif.Physics.PhysicalQuantities import PhysicalUnit as PU
import mupif.Physics.PhysicalQuantities as PQ
import math
import numpy as np

# check for python-vtk before running related tests
try:
    import vtk
    vtkAvailable=True
except ImportError:
    vtkAvailable=False



class Field_TestCase(unittest.TestCase):
    def setUp(self):
        
        self.mesh = Mesh.UnstructuredMesh()
        self.mesh.setup([Vertex.Vertex(0,0,(0.,0.,0.)), Vertex.Vertex(1,1,(2.,0.,0.)), Vertex.Vertex(2,2,(0.,5.,0.)), Vertex.Vertex(3,3,(4.,2.,0.))], [Cell.Triangle_2d_lin(self.mesh,1,1,(0,1,2)),Cell.Triangle_2d_lin(self.mesh,2,2,(1,2,3))])

        self.mesh3 = Mesh.UnstructuredMesh()
        self.mesh3.setup([Vertex.Vertex(0,16,(5.,6.,0.)), Vertex.Vertex(1,5,(8.,8.,0.)), Vertex.Vertex(2,8,(6.,10.,0.))], [Cell.Triangle_2d_lin(self.mesh3,3,8,(0,1,2))])
        
        self.mesh4 = Mesh.UnstructuredMesh()
        self.mesh4.setup([Vertex.Vertex(0,0,(0.,0.,0.)), Vertex.Vertex(1,1,(2.,0.,2.)), Vertex.Vertex(2,2,(0.,5.,3.)),Vertex.Vertex(3,3,(3.,3.,2.)),Vertex.Vertex(4,4,(8.,15.,0.))], [Cell.Tetrahedron_3d_lin(self.mesh4,1,1,(0,1,2,3)),Cell.Tetrahedron_3d_lin(self.mesh4,2,2,(1,2,3,4))])
        
        
        self.f1=Field.Field(self.mesh,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(13, 's'),[(0,),(12,),(175,),(94,)],1)
        self.f2=Field.Field(self.mesh,FieldID.FID_Strain,ValueType.Vector,PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),PQ.PhysicalQuantity(128,'s'),[(3,6),(2,8),(2,3)],1)
        self.f3=Field.Field(self.mesh,FieldID.FID_Stress,ValueType.Tensor,PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),PQ.PhysicalQuantity(66,'s'),[(3,6,4),(2,8,5),(2,3,6)],1)
        self.f4=Field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(6,),(16,),(36,),(33,),(32,)])
        self.f5=Field.Field(self.mesh3,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(13,'s'),[(3,),(5,),(4,)],1)
        self.f6=Field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(0,),(12,),(39,),(33,),(114,)])
        self.f7=Field.Field(self.mesh4,FieldID.FID_Displacement,ValueType.Scalar,PU({'m': 1}, 1,(1,0,0,0,0,0,0)),PQ.PhysicalQuantity(16,'s'),[(2,),(16,)],Field.FieldType.FT_cellBased)
        self.f8 = Field.Field(self.mesh, FieldID.FID_Displacement, ValueType.Scalar,
                              PU({'m': 1}, 1, (1, 0, 0, 0, 0, 0, 0)), PQ.PhysicalQuantity(13, 's'), None, 1)
        self.f9 = Field.Field(self.mesh, FieldID.FID_Displacement, ValueType.Scalar,
                              PU({'m': 1}, 1, (1, 0, 0, 0, 0, 0, 0)), PQ.PhysicalQuantity(13, 's'), None,
                              Field.FieldType.FT_cellBased)

        l = len(self.f8.value)
        self.assertEqual(l, self.mesh.getNumberOfVertices())
        l = len(self.f9.value)
        self.assertEqual(l, self.mesh.getNumberOfCells())


        #register assertEqual operation for PhysicalQuantities
        self.addTypeEqualityFunc(PQ.PhysicalQuantity, self.assertPhysicalQuantitiesEqual)
        
    def tearDown(self):
        
        self.f1 = None
        self.f2 = None
        self.f3 = None
        self.f4=None
        self.f5=None
        self.f6=None
        self.mesh = None
        self.mesh3=None
        self.mesh5=None


    # unit tests support
    def assertPhysicalQuantitiesEqual (self, first, second, msg=None):
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
        self.assertEqual(self.f1.getFieldType(),Field.FieldType.FT_vertexBased,'error in FieldType for f1')
        self.assertEqual(self.f7.getFieldType(),Field.FieldType.FT_cellBased,'error in FieldType for f4')
                
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
        # NB: PhysicalQuantity does not define __eq__ operator, hence string representation (name()) is compared
        self.assertEqual(self.f1.getUnits().name(),PU({'m': 1}, 1,(1,0,0,0,0,0,0)).name(),'error in getUnits for f1')
        self.assertEqual(self.f2.getUnits().name(),PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)).name(),'error in getUnits for f2')
        
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
       
    def test_field2VTKData(self):
       self.res=self.f5.field2VTKData()
       import pyvtk
       self.assertTrue(isinstance(self.res,pyvtk.VtkData),'error in getVTKRepresentation')       
        
    def test_dumpToLocalFile(self):
        with tempfile.NamedTemporaryFile(suffix='.dump') as tmp:
            self.f1.dumpToLocalFile(tmp.name)
            self.res=self.f1.loadFromLocalFile(tmp.name)
        self.assertEqual(self.res.getRecordSize(),self.f1.getRecordSize(), 'error in dumpToLocalFile(getRecordSize for res)')
        self.assertEqual(self.res.getValueType(),self.f1.getValueType(), 'error in dumpToLocalFile(getValueType for res)')    
        self.assertEqual(self.res.getFieldID(),self.f1.getFieldID(),'error in dumpToLocalFile(getFieldID for res)')
        self.assertEqual(self.res.getFieldIDName(),self.f1.getFieldIDName(),'error in dumpToLocalFile(getFieldIDName for res)')
        self.assertEqual(self.res.getTime().getValue(),self.f1.getTime().getValue(), 'error in dumpToLocalFile(getTime for res)')
        self.assertEqual(self.res.getVertexValue(0),self.f1.getVertexValue(0),'error in dumpToLocalFile(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(1),self.f1.getVertexValue(1),'error in dumpToLocalFile(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(2),self.f1.getVertexValue(2),'error in dumpToLocalFile(getVertexValue for res)')
        print(self.res.getUnits())
        print(self.f1.getUnits())
        self.assertEqual(self.res.getUnits().name(),self.f1.getUnits().name(),'error in dumpToLocalFile(getUnits for res)')
        
        self.f4.dumpToLocalFile('dump')
        self.res=self.f4.loadFromLocalFile('dump')
        self.assertEqual(self.res.getRecordSize(), self.f4.getRecordSize(), 'error in dumpToLocalFile(getRecordSize for res)')
        self.assertEqual(self.res.getValueType(),self.f4.getValueType(), 'error in dumpToLocalFile(getValueType for res)')
        self.assertEqual(self.res.getFieldID(),self.f4.getFieldID(),'error in dumpToLocalFile(getFieldID for res)')
        self.assertEqual(self.res.getFieldIDName(),self.f4.getFieldIDName(),'error in dumpToLocalFile(getFieldIDName for res)')
        self.assertEqual(self.res.getTime().getValue(),self.f4.getTime().getValue(), 'error in dumpToLocalFile(getTime for res)')
        self.assertEqual(self.res.getVertexValue(0),self.f4.getVertexValue(0),'error in dumpToLocalFile(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(1),self.f4.getVertexValue(1),'error in dumpToLocalFile(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(2),self.f4.getVertexValue(2),'error in dumpToLocalFile(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(3),self.f4.getVertexValue(3),'error in dumpToLocalFile(getVertexValue for res)')
        
    def test_toHdf5(self):
        with tempfile.NamedTemporaryFile(suffix='.hdf5') as tmp:
            self.f1.toHdf5(tmp.name)
            self.res=self.f1.makeFromHdf5(tmp.name)[0]
        self.assertEqual(self.res.getRecordSize(),self.f1.getRecordSize(), 'error in toHdf5(getRecordSize for res)')
        self.assertEqual(self.res.getValueType(),self.f1.getValueType(), 'error in toHdf5(getValueType for res)')    
        self.assertEqual(self.res.getFieldID(),self.f1.getFieldID(),'error in toHdf5(getFieldID for res)')
        self.assertEqual(self.res.getFieldIDName(),self.f1.getFieldIDName(),'error in toHdf5(getFieldIDName for res)')
        self.assertEqual(self.res.getTime().getValue(),self.f1.getTime().getValue(), 'error in toHdf5(getTime for res)')
        self.assertEqual(self.res.getVertexValue(0),self.f1.getVertexValue(0),'error in toHdf5(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(1),self.f1.getVertexValue(1),'error in toHdf5(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(2),self.f1.getVertexValue(2),'error in toHdf5(getVertexValue for res)')
        self.assertEqual(self.res.getUnits().name(),self.f1.getUnits().name(),'error in toHdf5(getUnits for res)')
        
    def test_toVTK2(self):
        with tempfile.NamedTemporaryFile(suffix='.vtk') as tmp:
            self.f1.toVTK2(tmp.name)
            self.res=self.f1.makeFromVTK2(tmp.name, PU({'m': 1}, 1,(1,0,0,0,0,0,0)), time=self.f1.getTime())[0]
        print(self.res)
        self.assertEqual(self.res.getRecordSize(),self.f1.getRecordSize(), 'error in toVTK2(getRecordSize for res)')
        self.assertEqual(self.res.getValueType(),self.f1.getValueType(), 'error in toVTK2(getValueType for res)')    
        self.assertEqual(self.res.getFieldID(),self.f1.getFieldID(),'error in toVTK2(getFieldID for res)')
        self.assertEqual(self.res.getFieldIDName(),self.f1.getFieldIDName(),'error in toVTK2(getFieldIDName for res)')
        self.assertEqual(self.res.getTime().getValue(),self.f1.getTime().getValue(), 'error in toVTK2(getTime for res)')
        # XXX: makeFromVTK2 returns 1-list, original field has 1-tuple
        # what is right?
        self.assertEqual(self.res.getVertexValue(0),self.f1.getVertexValue(0),'error in toVTK2(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(1),self.f1.getVertexValue(1),'error in toVTK2(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(2),self.f1.getVertexValue(2),'error in toVTK2(getVertexValue for res)')
        # VTK2 does not store units
        # self.assertEqual(self.res.getUnits(),self.f1.getUnits(),'error in toVTK2(getUnits for res)')
       
    @unittest.skipUnless(vtkAvailable,'vtk (python-vtk/python-vtk6) not importable') # vtkAvailable defined above
    def test_toVTK3(self):
        with tempfile.NamedTemporaryFile(suffix='.vtu') as tmp:
            self.f1.toVTK3(tmp.name)
            self.res=self.f1.makeFromVTK3(tmp.name,self.f1.getUnits(),time=self.f1.getTime())[0]
        self.assertEqual(self.res.getRecordSize(),self.f1.getRecordSize(), 'error in toVTK3(getRecordSize for res)')
        self.assertEqual(self.res.getValueType(),self.f1.getValueType(), 'error in toVTK3(getValueType for res)')    
        self.assertEqual(self.res.getFieldID(),self.f1.getFieldID(),'error in toVTK3(getFieldID for res)')
        self.assertEqual(self.res.getFieldIDName(),self.f1.getFieldIDName(),'error in toVTK3(getFieldIDName for res)')
        self.assertEqual(self.res.getTime().getValue(),self.f1.getTime().getValue(), 'error in toVTK3(getTime for res)')
        self.assertEqual(self.res.getVertexValue(0),self.f1.getVertexValue(0),'error in toVTK3(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(1),self.f1.getVertexValue(1),'error in toVTK3(getVertexValue for res)')
        self.assertEqual(self.res.getVertexValue(2),self.f1.getVertexValue(2),'error in toVTK3(getVertexValue for res)')
        # VTK3 does not store units
        # self.assertEqual(self.res.getUnits().name(),self.f1.getUnits().name(),'error in toVTK3(getUnits for res)')
        
        
# python test_Field.py for stand-alone test being run
if __name__=='__main__': unittest.main()
