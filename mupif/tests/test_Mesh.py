import unittest
import sys
sys.path.append('../..')

from mupif import *
import math
import numpy as np
import meshio
import types

def mkVertex(number,label,coords): return vertex.Vertex(number=number,label=label,coords=coords)
def mkCell(mesh,number,label,vertices): return cell.Cell(mesh=mesh,number=number,label=label,vertices=vertices)

try: import vtk
except ImportError: vtk=None

class UniformRectilinearMesh(unittest.TestCase):
    def setUp(self):
        self.m1=mesh.UniformRectilinearMesh(origin=(-3,-2,-1),spacing=(.3,.2,.1),dims=(5,4,3))
    def test_basic(self):
        self.assertEqual(self.m1.getNumberOfVertices(),60)
        self.assertEqual(self.m1.getNumberOfCells(),24)
        # from rich.pretty import pprint
        # pprint(dict([(i,self.m1.getVertex(i).coords) for i in range(0,self.m1.getNumberOfVertices())]))
        # self.assertTrue(False)
    # TODO: more tests

class Mesh_TestCase(unittest.TestCase):
    def setUp(self):

        self.mesh1 = mesh.UnstructuredMesh()
        self.mesh1.setup([mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(0.,5.))], [])

        self.mesh2 = mesh.UnstructuredMesh()
        self.mesh2.setup([mkVertex(0,0,(0.,0.,2.)), mkVertex(1,1,(2.,0.,2.)), mkVertex(2,2,(0.,5.,2.)),mkVertex(3,3,(3.,3.,2.))], [mkCell(self.mesh2,1,1,(0,1,2)),(mkCell(self.mesh2,2,2,(1,2,3)))])

        self.mesh3 = mesh.UnstructuredMesh()
        self.mesh3.setup([mkVertex(0,4,(1.,1.)), mkVertex(1,5,(3.,1.)), mkVertex(2,6,(3.,5.)), mkVertex(3,16,(8.,7.))], [cell.Triangle_2d_lin(mesh=self.mesh3,number=5,label=22,vertices=(0,1,2)),(cell.Triangle_2d_lin(mesh=self.mesh3,number=2,label=18,vertices=(1,2,3)))])

        self.mesh4 = mesh.UnstructuredMesh()
        self.mesh4.setup([mkVertex(0,4,(0.,0.,2.)), mkVertex(1,8,(2.,0.,2.)), mkVertex(2,16,(0.,5.,2.)),mkVertex(3,23,(3.,3.,2.))], [mkCell(self.mesh4,1,16,(0,1,2)),(mkCell(self.mesh4,2,18,(1,2,3)))])

        self.mesh5 = mesh.UnstructuredMesh()
        self.mesh5.setup([mkVertex(0,16,(8.,7.,0.)), mkVertex(1,5,(3.,1.,0.)), mkVertex(2,8,(35.,42.,0.)), mkVertex(3,9,(545.,72.,0.))], [cell.Triangle_2d_lin(mesh=self.mesh5,number=5,label=1,vertices=(0,1,2)),(cell.Triangle_2d_lin(mesh=self.mesh5,number=2,label=2,vertices=(1,2,3)))])

    def test_copy(self):
        self.res=self.mesh1.copy()
        self.assertEqual(self.mesh1.getNumberOfVertices(),self.res.getNumberOfVertices())
        self.assertEqual(self.mesh1.getNumberOfCells(),self.res.getNumberOfCells())

        self.res2=self.mesh2.copy()
        self.assertEqual(self.mesh2.getNumberOfVertices(),self.res2.getNumberOfVertices())
        self.assertEqual(self.mesh2.getNumberOfCells(),self.res2.getNumberOfCells())

    def test_getNumberOfVertices(self):
        self.assertEqual(self.mesh1.getNumberOfVertices(),3)
        self.assertEqual(self.mesh2.getNumberOfVertices(),4)
        self.assertEqual(self.mesh3.getNumberOfVertices(),4)

    def test_getNumberOfCells(self):
        self.assertEqual(self.mesh1.getNumberOfCells(),0)
        self.assertEqual(self.mesh2.getNumberOfCells(),2)
        self.assertEqual(self.mesh3.getNumberOfCells(),2)

    def test_getVertex(self):
        self.res=self.mesh1.getVertex(1)
        self.assertEqual(self.res.getCoordinates(),(2.,0.))
        self.assertEqual(self.res.getNumber(),1)

        self.res2=self.mesh2.getVertex(1)
        self.assertEqual(self.res2.getCoordinates(),(2.,0.,2.))
        self.assertEqual(self.res2.getNumber(),1)       

        self.res2=self.mesh2.getVertex(0)
        self.assertEqual(self.res2.getCoordinates(),(0.,0.,2.))
        self.assertEqual(self.res2.getNumber(),0)

    def test_getCell(self):
        self.res=self.mesh2.getCell(0)
        self.assertEqual(self.res.getNumberOfVertices(),3)
        self.assertEqual(self.res.getVertices(),mkCell(self.mesh2,1,1,(0,1,2)).getVertices())

        self.res=self.mesh4.getCell(1)
        self.assertEqual(self.res.getNumberOfVertices(),3)
        self.assertEqual(self.res.getVertices(),mkCell(self.mesh4,2,2,(1,2,3)).getVertices())

        self.res=self.mesh3.getCell(0)
        self.assertEqual(self.res.getNumberOfVertices(),3)
        self.assertEqual(self.res.getVertices(),mkCell(self.mesh3,5,22,(0,1,2)).getVertices())        
    def test_getVertexLocalizer(self):
        self.res=self.mesh2.getVertexLocalizer()
        s=self.res.getItemsInBBox(bbox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertEqual(s,{0,1,2,3})

        self.res=self.mesh5.getVertexLocalizer()
        s=self.res.getItemsInBBox(bbox.BBox((3.,1.,0.),(545.,72.,0.)))
        self.assertEqual(s,{0,1,2,3})

    def test_getCellLocalizer(self):
        self.res=self.mesh2.getCellLocalizer()
        s=self.res.getItemsInBBox(bbox.BBox((0.,0.,2.),(3.,5.,2.)))
        self.assertTrue(1 in s)
        self.assertTrue(0 in s)

        self.res=self.mesh5.getCellLocalizer()
        s=self.res.getItemsInBBox(bbox.BBox((3.,1.,0.),(545.,72.,0.)))
        self.assertTrue(1 in s)
        self.assertTrue(0 in s)

    def test_vertexLabel2Number(self):
        self.assertEqual(self.mesh4.vertexLabel2Number(4),0)
        self.assertEqual(self.mesh4.vertexLabel2Number(16),2)
        self.assertEqual(self.mesh3.vertexLabel2Number(4),0)

    def test_cellLabel2Number(self):
        self.assertEqual(self.mesh4.cellLabel2Number(16),0)
        self.assertEqual(self.mesh4.cellLabel2Number(18),1)
        self.assertEqual(self.mesh3.cellLabel2Number(22),0)

    def test_merge(self):
        self.mesh3.merge(self.mesh5)
        self.assertEqual(self.mesh3.getCell(0).getVertices()[1].label, 5)
        self.assertEqual(self.mesh3.getCell(0).getVertices()[2].label, 6)
        self.assertEqual(self.mesh3.getCell(2).getVertices()[0].label, 16)
        self.assertEqual(self.mesh3.getCell(2).getVertices()[1].label, 5)

    @unittest.skipIf(vtk is None,'vtk not importable')
    def test_asVtkUnstructuredGrid(self):
        # @todo: not working with mesh1 because points have only two coordinates
        # @todo: not working with mesh4 because cell types are not supported ?
        self.testMesh = mesh.UnstructuredMesh()
        self.testMesh.setup([mkVertex(0, 0, (0., 0., 0.)), mkVertex(1, 1, (1., 0., 0.)), mkVertex(2, 2, (1., 1., 0)),
                             mkVertex(3, 3, (0., 1., 0.)), mkVertex(4, 4, (0., 0., 1.)), mkVertex(5, 5, (1., 0., 1.)),
                             mkVertex(6, 6, (1., 1., 0)),
                             mkVertex(7, 7, (0., 1., 1.))], [cell.Brick_3d_lin(mesh=self.testMesh, number=1, label=1, vertices=(0, 1, 2, 3, 4, 5, 6, 7))])
        self.testMesh.asVtkUnstructuredGrid()

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
