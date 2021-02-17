import unittest
import sys
sys.path.append('../..')

from mupif import *
import math
import numpy as np
import meshio
import types

try: import vtk
except ImportError: vtk=None


class Mesh_TestCase(unittest.TestCase):
    def setUp(self):
        
        self.mesh1 = mesh.UnstructuredMesh()
        self.mesh1.setup([vertex.Vertex(0,0,(0.,0.)), vertex.Vertex(1,1,(2.,0.)), vertex.Vertex(2,2,(0.,5.))], [])
        
        self.mesh2 = mesh.UnstructuredMesh()
        self.mesh2.setup([vertex.Vertex(0,0,(0.,0.,2.)), vertex.Vertex(1,1,(2.,0.,2.)), vertex.Vertex(2,2,(0.,5.,2.)),vertex.Vertex(3,3,(3.,3.,2.))], [cell.Cell(self.mesh2,1,1,(0,1,2)),(cell.Cell(self.mesh2,2,2,(1,2,3)))])
        
        self.mesh3 = mesh.UnstructuredMesh()
        self.mesh3.setup([vertex.Vertex(0,4,(1.,1.)), vertex.Vertex(1,5,(3.,1.)), vertex.Vertex(2,6,(3.,5.)), vertex.Vertex(3,16,(8.,7.))], [cell.Triangle_2d_lin(self.mesh3,5,22,(0,1,2)),(cell.Triangle_2d_lin(self.mesh3,2,18,(1,2,3)))])
        
        self.mesh4 = mesh.UnstructuredMesh()
        self.mesh4.setup([vertex.Vertex(0,4,(0.,0.,2.)), vertex.Vertex(1,8,(2.,0.,2.)), vertex.Vertex(2,16,(0.,5.,2.)),vertex.Vertex(3,23,(3.,3.,2.))], [cell.Cell(self.mesh4,1,16,(0,1,2)),(cell.Cell(self.mesh4,2,18,(1,2,3)))])
        
        self.mesh5 = mesh.UnstructuredMesh()
        self.mesh5.setup([vertex.Vertex(0,16,(8.,7.,0.)), vertex.Vertex(1,5,(3.,1.,0.)), vertex.Vertex(2,8,(35.,42.,0.)), vertex.Vertex(3,9,(545.,72.,0.))], [cell.Triangle_2d_lin(self.mesh5,5,1,(0,1,2)),(cell.Triangle_2d_lin(self.mesh5,2,2,(1,2,3)))])
 
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
        self.assertEqual(self.res.getVertices(),cell.Cell(self.mesh2,1,1,(0,1,2)).getVertices(),'error in getCell(getVertices,mesh2_Cell(0))')

        self.res=self.mesh4.getCell(1)
        self.assertEqual(self.res.getNumberOfVertices(),3,'error in getCell(getNumberOfVertices),mesh4_Cell(1)')
        self.assertEqual(self.res.getVertices(),cell.Cell(self.mesh4,2,2,(1,2,3)).getVertices(),'error in getCell(getVertices),mesh4_Cell(1)')

        self.res=self.mesh3.getCell(0)
        self.assertEqual(self.res.getNumberOfVertices(),3,'error in getCell(getNumberOfVertices),mesh3_Cell(0)')
        self.assertEqual(self.res.getVertices(),cell.Cell(self.mesh3,5,22,(0,1,2)).getVertices(),'error in getCell(getVertices),mesh3_Cell(0)')        
#Testing giveVertexLocalizer
    def test_giveVertexLocalizer(self):
        self.res=self.mesh2.giveVertexLocalizer()
        s=self.res.giveItemsInBBox(bbox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertEqual(self.mesh2.getVertex(1) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(0) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(2) in s,True,'error in giveVertexLocalizer mesh2')
        self.assertEqual(self.mesh2.getVertex(3) in s,True,'error in giveVertexLocalizer mesh2')
        
        self.res=self.mesh5.giveVertexLocalizer()
        s=self.res.giveItemsInBBox(bbox.BBox((3.,1.,0.),(545.,72.,0.)))
        self.assertEqual(self.mesh5.getVertex(1) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(0) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(2) in s,True,'error in giveVertexLocalizer mesh5')
        self.assertEqual(self.mesh5.getVertex(3) in s,True,'error in giveVertexLocalizer mesh5')
        
#Testing giveVertexLocalizer
    def test_giveCellLocalizer(self):
        self.res=self.mesh2.giveCellLocalizer()
        s=self.res.giveItemsInBBox(bbox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertEqual(self.mesh2.getCell(1) in s,True,'error in giveCellLocalizer mesh2')
        self.assertEqual(self.mesh2.getCell(0) in s,True,'error in giveCellLocalizer mesh2')
        
        self.res=self.mesh5.giveCellLocalizer()
        s=self.res.giveItemsInBBox(bbox.BBox((3.,1.,0.),(545.,72.,0.)))
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
    def test_merge(self):
        self.mesh3.merge(self.mesh5)
        self.assertEqual(self.mesh3.getCell(0).getVertices()[1].label, 5, 'error in merge')
        self.assertEqual(self.mesh3.getCell(0).getVertices()[2].label, 6, 'error in merge')
        self.assertEqual(self.mesh3.getCell(2).getVertices()[0].label, 16, 'error in merge')
        self.assertEqual(self.mesh3.getCell(2).getVertices()[1].label, 5, 'error in merge')
    
    @unittest.skipIf(vtk is None,'vtk not importable')
    def test_asVtkUnstructuredGrid(self):
        # @todo: not working with mesh1 because points have only two coordinates
        # @todo: not working with mesh4 because cell types are not supported ?
        self.testMesh = mesh.UnstructuredMesh()
        self.testMesh.setup([vertex.Vertex(0, 0, (0., 0., 0.)), vertex.Vertex(1, 1, (1., 0., 0.)), vertex.Vertex(2, 2, (1., 1., 0)),
                             vertex.Vertex(3, 3, (0., 1., 0.)), vertex.Vertex(4, 4, (0., 0., 1.)), vertex.Vertex(5, 5, (1., 0., 1.)),
                             vertex.Vertex(6, 6, (1., 1., 0)),
                             vertex.Vertex(7, 7, (0., 1., 1.))], [cell.Brick_3d_lin(self.testMesh, 1, 1, (0, 1, 2, 3, 4, 5, 6, 7))])
        self.testMesh.asVtkUnstructuredGrid()

    #Testing getVTKRepresentation
    def test_getVTKRepresentation(self):
        pp,cc=self.mesh5.toMeshioPointsCells()
        self.assertEqual(pp.shape,(4,3))
        self.assertEqual('triangle',cc[0][0])
        self.assertEqual(len(cc[0][1]),2)
       # self.assertTrue(isinstance(self.res,meshio.Mesh))
       #self.res=self.mesh5.getVTKRepresentation()
       #import pyvtk
       #self.assertTrue(isinstance(self.res,pyvtk.DataSet.DataSet),'error in getVTKRepresentation')
  
# python test_Mesh.py for stand-alone test being run
if __name__=='__main__': unittest.main()
