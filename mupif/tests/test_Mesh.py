import unittest
from mupif import *
import math
import numpy as np
import pyvtk
import types

class Mesh_TestCase(unittest.TestCase):
    def setUp(self):
        
        self.mesh1 = Mesh.UnstructuredMesh()
        self.mesh1.setup([Vertex.Vertex(0,0,(0.,0.)), Vertex.Vertex(1,1,(2.,0.)), Vertex.Vertex(2,2,(0.,5.))], [])
        
        self.mesh2 = Mesh.UnstructuredMesh()
        self.mesh2.setup([Vertex.Vertex(0,0,(0.,0.,2.)), Vertex.Vertex(1,1,(2.,0.,2.)), Vertex.Vertex(2,2,(0.,5.,2.)),Vertex.Vertex(3,3,(3.,3.,2.))], [Cell.Cell(self.mesh2,1,1,(0,1,2)),(Cell.Cell(self.mesh2,2,2,(1,2,3)))])
        
        self.mesh3 = Mesh.UnstructuredMesh()
        self.mesh3.setup([Vertex.Vertex(0,4,(1.,1.)), Vertex.Vertex(1,5,(3.,1.)), Vertex.Vertex(2,6,(3.,5.)), Vertex.Vertex(3,16,(8.,7.))], [Cell.Triangle_2d_lin(self.mesh3,5,22,(0,1,2)),(Cell.Triangle_2d_lin(self.mesh3,2,18,(1,2,3)))])
        
        self.mesh4 = Mesh.UnstructuredMesh()
        self.mesh4.setup([Vertex.Vertex(0,4,(0.,0.,2.)), Vertex.Vertex(1,8,(2.,0.,2.)), Vertex.Vertex(2,16,(0.,5.,2.)),Vertex.Vertex(3,23,(3.,3.,2.))], [Cell.Cell(self.mesh4,1,16,(0,1,2)),(Cell.Cell(self.mesh4,2,18,(1,2,3)))])
        
        self.mesh5 = Mesh.UnstructuredMesh()
        self.mesh5.setup([Vertex.Vertex(11,16,(8.,7.,0.)), Vertex.Vertex(15,5,(3.,1.,0.)), Vertex.Vertex(31,8,(35.,42.,0.)), Vertex.Vertex(35,9,(545.,72.,0.))], [Cell.Triangle_2d_lin(self.mesh5,5,1,(0,1,2)),(Cell.Triangle_2d_lin(self.mesh5,2,2,(1,2,3)))])
 
    def tearDown(self):
        
        self.mesh1=None
        self.mesh2=None
        self.mesh3=None
        self.mesh4=None
        self.mesh5=None

    #Testing copy (vertexList.append(copy.deepcopy(v))NameError: global name 'v' is not defined)
    def test_copy(self):
        self.res=self.mesh1.copy()
        self.assertEqual(self.mesh1.getNumberOfVertices(),self.res.getNumberOfVertices(),'error in copy for mesh1')
        self.assertEqual(self.mesh1.getNumberOfCells(),self.res.getNumberOfCells(),'error in copy for mesh1')
        
        self.res2=self.mesh2.copy()
        self.assertEqual(self.mesh2.getNumberOfVertices(),self.res2.getNumberOfVertices(),'error in copy for mesh1')
        self.assertEqual(self.mesh2.getNumberOfCells(),self.res2.getNumberOfCells(),'error in copy for mesh1')

#Testing getNumberOfVertices
    def test_getNumberOfVertices(self):
        self.assertEqual(self.mesh1.getNumberOfVertices(),3,'error in getNumberofVertices for mesh1')
        self.assertEqual(self.mesh2.getNumberOfVertices(),4,'error in getNumberofVertices for mesh2')
        self.assertEqual(self.mesh3.getNumberOfVertices(),4,'error in getNumberofVertices for mesh3')
        
#Testing getNumberOfCells
    def test_getNumberOfCells(self):
        self.assertEqual(self.mesh1.getNumberOfCells(),0,'error in getNumberofCells for mesh1')
        self.assertEqual(self.mesh2.getNumberOfCells(),2,'error in getNumberofCells for mesh2')
        self.assertEqual(self.mesh3.getNumberOfCells(),2,'error in getNumberofCells for mesh3')
        
#Testing getVertex
    def test_getVertex(self):
        self.res=self.mesh1.getVertex(1)
        self.assertEqual(self.res.getCoordinates(),(2.,0.),'error in getVertex for mesh1(1)')
        self.assertEqual(self.res.getNumber(),1,'error in getVertex for mesh1(1)')
        
        self.res2=self.mesh2.getVertex(1)
        self.assertEqual(self.res2.getCoordinates(),(2.,0.,2.),'error in getVertex for mesh2(1)')
        self.assertEqual(self.res2.getNumber(),1,'error in getVertex for mesh2(1)')       
        
        self.res2=self.mesh2.getVertex(0)
        self.assertEqual(self.res2.getCoordinates(),(0.,0.,2.),'error in getVertex for mesh2(0)')
        self.assertEqual(self.res2.getNumber(),0,'error in getVertex for mesh2(0)')
        
#Testing getCell
    def test_getCell(self):
        self.res=self.mesh2.getCell(0)
        self.assertEqual(self.res.getNumberOfVertices(),3,'error in getCell(getNumberOfVertices),mesh2_Cell(0)')
        self.assertEqual(self.res.getVertices(),Cell.Cell(self.mesh2,1,1,(0,1,2)).getVertices(),'error in getCell(getVertices,mesh2_Cell(0))')

        self.res=self.mesh4.getCell(1)
        self.assertEqual(self.res.getNumberOfVertices(),3,'error in getCell(getNumberOfVertices),mesh4_Cell(1)')
        self.assertEqual(self.res.getVertices(),Cell.Cell(self.mesh4,2,2,(1,2,3)).getVertices(),'error in getCell(getVertices),mesh4_Cell(1)')

        self.res=self.mesh3.getCell(0)
        self.assertEqual(self.res.getNumberOfVertices(),3,'error in getCell(getNumberOfVertices),mesh3_Cell(0)')
        self.assertEqual(self.res.getVertices(),Cell.Cell(self.mesh3,5,22,(0,1,2)).getVertices(),'error in getCell(getVertices),mesh3_Cell(0)')        
#Testing giveVertexLocalizer
    def test_giveVertexLocalizer(self):
        self.res=self.mesh2.giveVertexLocalizer()
        s=self.res.giveItemsInBBox(BBox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertEqual(self.mesh2.getVertex(1) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(0) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(2) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(3) in s,True,'error in giveVertexLocalizer mesh2')
        
        self.res=self.mesh5.giveVertexLocalizer()
        s=self.res.giveItemsInBBox(BBox.BBox((3.,1.,0.),(545.,72.,0.)))
        self.assertEqual(self.mesh5.getVertex(1) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(0) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(2) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(3) in s,True,'error in giveVertexLocalizer mesh5')
        
#Testing giveVertexLocalizer
    def test_giveCellLocalizer(self):
        self.res=self.mesh2.giveCellLocalizer()
        s=self.res.giveItemsInBBox(BBox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertEqual(self.mesh2.getCell(1) in s,True,'error in giveCellLocalizer mesh2')
        self.assertEqual(self.mesh2.getCell(0) in s,True,'error in giveCellLocalizer mesh2')
        
        self.res=self.mesh5.giveCellLocalizer()
        s=self.res.giveItemsInBBox(BBox.BBox((3.,1.,0.),(545.,72.,0.)))
        self.assertEqual(self.mesh5.getCell(1) in s,True,'error in giveCellLocalizer mesh5')
        self.assertEqual(self.mesh5.getCell(0) in s,True,'error in giveCellLocalizer mesh5')

#Testing vertexLabel2Number
    def test_vertexLabel2Number(self):
        self.assertEqual(self.mesh4.vertexLabel2Number(4),0,'error in vertexLabel2Number for mesh4(4)')
        self.assertEqual(self.mesh4.vertexLabel2Number(16),2,'error in vertexLabel2Number for mesh4(16)')
        self.assertEqual(self.mesh3.vertexLabel2Number(4),0,'error in vertexLabel2Number for mesh3(4)')
        
#Testing vertexLabel2Number
    def test_cellLabel2Number(self):
        self.assertEqual(self.mesh4.cellLabel2Number(16),0,'error in cellLabel2Number for mesh4(16)')
        self.assertEqual(self.mesh4.cellLabel2Number(18),1,'error in cellLabel2Number for mesh4(18)')
        self.assertEqual(self.mesh3.cellLabel2Number(22),0,'error in cellLabel2Number for mesh4(1)')
        
#Testing merge (AttributeError: 'Triangle_2d_lin' object has no attribute 'giveVertices')
#    def test_merge(self):
#        self.mesh3.merge(self.mesh5)
        
#Testing getVTKRepresentation      
    def test_getVTKRepresentation(self):
       self.res=self.mesh5.getVTKRepresentation()
       self.assertEqual(type(self.res) is types.InstanceType,True,'error in getVTKRepresentation')
  
# python test_Mesh.py for stand-alone test being run
if __name__=='__main__': unittest.main()
