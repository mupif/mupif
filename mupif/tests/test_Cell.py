import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
import numpy as np

def mkVertex(number,label,coords): return vertex.Vertex(number=number,label=label,coords=coords)

class Triangle_2d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(0.,5.))), [])
        self.cell = cell.Triangle_2d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2))

    def tearDown(self):
        self.mesh = None
        self.cell = None

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TRIANGLE_1, 'wrong geometry type')

    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.))
        self.assertEqual(gc1, (1.0, 0.,0.), 'error in glob2loc for vertex 1 (0,0)') 

        gc1 = self.cell.glob2loc((2.,0.))
        self.assertEqual(gc1, (0., 1.,0.), 'error in glob2loc for vertex 2 (2,0)') 

        gc1 = self.cell.glob2loc((0.,5.))
        self.assertEqual(gc1, (0.,0., 1.0), 'error in glob2loc for vertex 3 (0,5)') 
        
        #test midside nodes
        gc1 = self.cell.glob2loc((1.,0.))
        self.assertEqual(gc1, (0.5, 0.5,0.), 'error in glob2loc for (1,0)') 

        gc1 = self.cell.glob2loc((1.,2.5))
        self.assertEqual(gc1, (0., 0.5,0.5), 'error in glob2loc for (1,2.5)') 

        gc1 = self.cell.glob2loc((0.,2.5))
        self.assertEqual(gc1, (0.5,0., 0.5), 'error in glob2loc for (0,2.5)') 

        #test center
        gc1 = self.cell.glob2loc((2.0/3.0,5.0/3.0))
        self.assertAlmostEqual(gc1[0], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[1], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[2], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        
    def test_loc2glob(self):
        gc = self.cell.loc2glob((0.2, 0.2))
        self.assertAlmostEqual(gc[0], 0.2*2, msg='error in loc2glob (0.2,0.2)', delta=1.e-5) 
        self.assertAlmostEqual(gc[1], 0.6*5, msg='error in loc2glob (0.2,0.2)', delta=1.e-5) 
       

    def test_interpolate(self):
        r = self.cell.interpolate((1.0,0.0), ((3.0,), (5.0,),(11.,)))
        self.assertAlmostEqual(r[0], 4.0, msg='error in interpolate', delta=1.e-5) 
        r = self.cell.interpolate((0.0,1.0), ((3.0,), (5.0,), (11.,)))
        self.assertAlmostEqual(r[0], 4./5.*3.0+1./5.*11., msg='error in interpolate', delta=1.e-5) 
        
    def test_containsPoint(self):
        b = self.cell.containsPoint((0.1, 0.0))
        self.assertTrue(b)
        b = self.cell.containsPoint((0., 0.2))
        self.assertTrue(b)
        b = self.cell.containsPoint((0., 5.1))
        self.assertFalse(b)

    def test_getTransformationJacobian(self):
        J = self.cell.getTransformationJacobian([])
        self.assertAlmostEqual(J, 10, msg='error in getTransformationJacobian', delta=1.e-8)

    def test_evalN(self):
        lc = (0.5, 0.5)
        N = self.cell._evalN(lc)
        self.assertAlmostEqual(N[0], 0.5, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[1], 0.5, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[2], 0.0, msg='error in _evalN', delta=1.e-5)



class Triangle_2d_quad_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(0.,5.)), mkVertex(3,3,(1.,0.)), mkVertex(4,4,(1.,2.5)), mkVertex(5,5,(0.,2.5))), [])
        self.cell = cell.Triangle_2d_quad(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3,4,5))

    def tearDown(self):
        self.mesh = None
        self.cell = None

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TRIANGLE_2, 'wrong geometry type')

    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.))
        self.assertEqual(gc1, (1.0, 0.,0.), 'error in glob2loc for vertex 1 (0,0)') 

        gc1 = self.cell.glob2loc((2.,0.))
        self.assertEqual(gc1, (0., 1.,0.), 'error in glob2loc for vertex 2 (2,0)') 

        gc1 = self.cell.glob2loc((0.,5.))
        self.assertEqual(gc1, (0.,0., 1.0), 'error in glob2loc for vertex 3 (0,5)') 
        
        #test midside nodes
        gc1 = self.cell.glob2loc((1.,0.))
        self.assertEqual(gc1, (0.5, 0.5,0.), 'error in glob2loc for (1,0)') 

        gc1 = self.cell.glob2loc((1.,2.5))
        self.assertEqual(gc1, (0., 0.5,0.5), 'error in glob2loc for (1,2.5)') 

        gc1 = self.cell.glob2loc((0.,2.5))
        self.assertEqual(gc1, (0.5,0., 0.5), 'error in glob2loc for (0,2.5)') 

        #test center
        gc1 = self.cell.glob2loc((2.0/3.0,5.0/3.0))
        self.assertAlmostEqual(gc1[0], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[1], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[2], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        
    def test_loc2glob(self):
        gc = self.cell.loc2glob((0.2, 0.2))
        self.assertAlmostEqual(gc[0], 0.2*2, msg='error in loc2glob (0.2,0.2)', delta=1.e-5) 
        self.assertAlmostEqual(gc[1], 0.6*5, msg='error in loc2glob (0.2,0.2)', delta=1.e-5) 
       

    def test_interpolate(self):
        r = self.cell.interpolate((1.0,0.0), ((3.0,),(5.0,), (11.,), (4.0,), (8.0,), (7.0,)))
        self.assertAlmostEqual(r[0], 4.0, msg='error in interpolate', delta=1.e-5) 
        r = self.cell.interpolate((0.0,1.0), ((3.0,),(5.0,), (11.,), (4.0,), (8.0,), (7.0,)))
        self.assertAlmostEqual(r[0], 4./5.*3.0+1./5.*11., msg='error in interpolate', delta=1.e-5) 
        
    def test_containsPoint(self):
        b = self.cell.containsPoint((0.1, 0.0))
        self.assertTrue(b)
        b = self.cell.containsPoint((0., 0.2))
        self.assertTrue(b)
        b = self.cell.containsPoint((0., 5.1))
        self.assertFalse(b)

    def test_evalN(self):
        l1 = 0.5
        l2 = 0.5
        l3 = 1 - l1 - l2
        lc = (l1, l2)
        N = self.cell._evalN(lc)
        self.assertAlmostEqual(N[0], (2. * l1 - 1.) * l1, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[1], (2. * l2 - 1.) * l2, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[2], (2. * l3 - 1.) * l3, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[3], 4. * l1 * l2, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[4], 4. * l2 * l3, msg='error in _evalN', delta=1.e-5)
        self.assertAlmostEqual(N[5], 4. * l3 * l1, msg='error in _evalN', delta=1.e-5)
        
class Quad_2d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh=mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(4.,2.)), mkVertex(3,3,(0.,5.))), [])
        self.cell = cell.Quad_2d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3))

    def tearDown(self):
        self.mesh = None
        self.cell = None
        
    def test_copy(self):
        self.c = self.cell.copy()
        gc1 = self.c.glob2loc((0.,0.))
        self.assertTupleEqual(gc1,(True,(1.0,1.0)),'error in glob2loc for vertex(0,0)')
        gc3 = self.c.glob2loc((4.,2.))
        self.assertTupleEqual(gc3,(True,(-1.0,-1.0)),'error in glob2loc for vertex(0,5)')
        gc1 = self.c.glob2loc((1.,0.))
        self.assertTupleEqual(gc1,(True,(0.,1.)),'error in glob2loc for vertex(1,0)')
        r = self.c.interpolate((2.,2.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],2,msg='error in interpolate for vertex (2,2)',delta=1.e-5)
        self.assertEqual(self.c.containsPoint((0.,5.)),True,'Error in contains point(0.,5.)')
        
        
    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_QUAD, 'wrong geometry type')
        
    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.))
        self.assertAlmostEqual(gc1[0], True, msg='error in glob2loc for vertex 1 (0,0)',delta=1.e-5)
        self.assertTupleEqual(gc1,(True,(1.0,1.0)),'error in glob2loc for vertex(0,0)')
        
        gc2 = self.cell.glob2loc((2.,0.))
#        print self.cell.glob2loc((2.,0.))
        self.assertEqual(gc2[0], True, msg='error in glob2loc for vertex (2,0)')
        self.assertAlmostEqual(gc2[1][0], -1.0, msg='error in glob2loc for vertex (2,0)', delta=1.e-5)
        self.assertAlmostEqual(gc2[1][1],  1.0, msg='error in glob2loc for vertex (2,0)', delta=1.e-5)
        
        gc3 = self.cell.glob2loc((4.,2.))
        self.assertTupleEqual(gc3,(True,(-1.0,-1.0)),'error in glob2loc for vertex(0,5)')
        
        gc4 = self.cell.glob2loc((0.,5.))
        self.assertTupleEqual(gc4,(True,(1.0,-1.0)),'error in glob2loc for vertex(4,2)')
        
         #test midside nodes
        gc1 = self.cell.glob2loc((1.,0.))
        self.assertTupleEqual(gc1,(True,(0.,1.)),'error in glob2loc for (1,0)')
        
        gc2 = self.cell.glob2loc((0.,2.5))
        self.assertTupleEqual(gc2,(True,(1.,0.)),'error in glob2loc for (0,2.5)')

        gc3 = self.cell.glob2loc((3.,1.))
        self.assertTupleEqual(gc3, (True,(-1., 0.)), 'error in glob2loc for (3,1)') 
        
        gc4 = self.cell.glob2loc((2.,3.5))
        self.assertTupleEqual(gc4, (True,(0.,-1.)), 'error in glob2loc for (2,3.5)') 

    def test_loc2glob(self):
        gc1 = self.cell.loc2glob((0.,1.))        
        self.assertEqual(gc1,(1.,0.),'error in loc2glob for vertex (1,0)')
        
        gc2 = self.cell.loc2glob((-1.0,-1.0))
        self.assertEqual(gc2,(4.,2.),'error in loc2glob for vertex (4,2)')
        
    def test_interpolate(self):
        r = self.cell.interpolate((2.,2.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],2,msg='error in interpolate for vertex (2,2)',delta=1.e-5)
        
        r = self.cell.interpolate((0.,3.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],-18,msg='error in interpolate for vertex (2,2)',delta=1.e-5)
        
    def test_containsPoint(self):
        self.assertEqual(self.cell.containsPoint((2.,2.)),True,'Error in contains point(2,2)')
        self.assertEqual(self.cell.containsPoint((0.,-0.2)),False,'Error in contains point(0.,-0.2)')
        self.assertEqual(self.cell.containsPoint((0.,5.)),True,'Error in contains point(0.,5.)')
        self.assertEqual(self.cell.containsPoint((4.01,2.)),False,'Error in contains point(4.01,2.)')
        
    def test_getTransformationJacobian(self):
        self.assertEqual(self.cell.getTransformationJacobian((1.0,1.0)),2.5,'error in getTransformationJacobian for (1.0,1.0)')
        self.assertEqual(self.cell.getTransformationJacobian((-1.0,-1.0)),3.5,'error in getTransformationJacobian for (-1.0,-1.0)')        
        self.assertEqual(self.cell.getTransformationJacobian((1.0,-1.0)),5.0,'error in getTransformationJacobian for (1.0,-1.0)')        
        self.assertEqual(self.cell.getTransformationJacobian((-1., 0.)),2.25,'error in getTransformationJacobian for (-1.0,0)')        
        
class Tetrahedron_3d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh=mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.,0.)), mkVertex(1,1,(2.,0.,3.)), mkVertex(2,2,(4.,2.,1.)), mkVertex(3,3,(0.,5.,5.))), [])
        self.cell = cell.Tetrahedron_3d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3))
        
        self.mesh2=mesh.UnstructuredMesh()
        self.mesh2.setup((mkVertex(0,0,(0.,0.,0.)), mkVertex(1,1,(0.,2.,0.)), mkVertex(2,2,(4.,0.,0.)), mkVertex(3,3,(0.,0.,6.))), [])
        self.cell2 = cell.Tetrahedron_3d_lin(mesh=self.mesh2, number=0, label=1, vertices=(0,1,2,3))

    def tearDown(self):
        self.mesh = None
        self.cell = None
        
        self.mesh2 = None
        self.cell2 = None
        
    def test_copy(self):
        self.r = self.cell.copy()
        self.assertEqual(self.r.getGeometryType(), cellgeometrytype.CGT_TETRA, 'wrong geometry type')
        gc1 = self.r.glob2loc((0.,0.,0.))
        self.assertEqual(gc1,(1.0,0.0,0.0,0.0),'error in glob2loc for vertex 1 (0,0,0)')
        gc2 = self.r.glob2loc((2.,0.,3.))
        self.assertEqual(gc2,(0.0,1.0,0.0,0.0),'error in glob2loc for vertex 2 (2,0,3)')
        gc5 = self.r.glob2loc((2.,3.5,3.))
        self.assertEqual(gc5,(0.0,0.0,0.5,0.5),'error in glob2loc for (2,3.5,3)')
        gc6 = self.r.glob2loc((1.,2.5,4.))
        self.assertEqual(gc6,(0.0,0.5,0.0,0.5),'error in glob2loc for (1,2.5,4)')
        r = self.r.interpolate((2.,2.,1.),((0.,),(18.,),(20.,),(-5.,)))
        self.assertAlmostEqual(r[0], 8., msg='error in interpolate for vertex (2,0,1)', delta=1.e-5) 
        
    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TETRA, 'wrong geometry type')
        
    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.,0.))
        self.assertEqual(gc1,(1.0,0.0,0.0,0.0),'error in glob2loc for vertex 1 (0,0,0)')
        
        gc2 = self.cell.glob2loc((2.,0.,3.))
        self.assertEqual(gc2,(0.0,1.0,0.0,0.0),'error in glob2loc for vertex 2 (2,0,3)')
        
        gc3 = self.cell.glob2loc((4.,2.,1.))
        self.assertEqual(gc3,(0.0,0.0,1.0,0.0),'error in glob2loc for vertex 3 (4,2,1)')
        
        gc4 = self.cell.glob2loc((0.,5.,5.))
        self.assertEqual(gc4,(0.0,0.0,0.0,1.0),'error in glob2loc for vertex 4 (0,5,5)')
        
        #test midside nodes
        gc1 = self.cell.glob2loc((1.,0.,1.5))
        self.assertEqual(gc1,(0.5,0.5,0.0,0.0),'error in glob2loc for (1,0,1.5)')
        
        gc2 = self.cell.glob2loc((2.,1.,0.5))
        self.assertEqual(gc2,(0.5,0.0,0.5,0.0),'error in glob2loc for (2,1,0.5)')
        
        gc3 = self.cell.glob2loc((0.,2.5,2.5))
        self.assertEqual(gc3,(0.5,0.0,0.0,0.5),'error in glob2loc for (0,2.5,2.5)')
        
        gc4 = self.cell.glob2loc((3.,1.,2.))
        self.assertEqual(gc4,(0.0,0.5,0.5,0.0),'error in glob2loc for (3,1,2)')
        
        gc5 = self.cell.glob2loc((2.,3.5,3.))
        self.assertEqual(gc5,(0.0,0.0,0.5,0.5),'error in glob2loc for (2,3.5,3)')
        
        gc6 = self.cell.glob2loc((1.,2.5,4.))
        self.assertEqual(gc6,(0.0,0.5,0.0,0.5),'error in glob2loc for (1,2.5,4)')
        
        #test center
        gc1 = self.cell2.glob2loc((4.0/3.0,2.0/3.0,6.0/3.0))
        self.assertAlmostEqual(gc1[0], 0, msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[1], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[2], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        self.assertAlmostEqual(gc1[3], 1./3., msg='error in glob2loc for element center', delta=1.e-5) 
        
    def test_loc2glob(self):
        #test vertices
        lg1 = self.cell.loc2glob((1.0,0.0,0.0,0.0))
        self.assertEqual(lg1,(0.,0.,0.),'error in loc2glob for vertex 1 (0,0,0)')
        
        lg3 = self.cell.loc2glob((0.0,0.0,1.0,0.0))
        self.assertEqual(lg3,(4.,2.,1.),'error in loc2glob for vertex 3 (4,2,1)')
        
        #test midside nodes
        lg1 = self.cell.loc2glob((0.5,0.5,0.0,0.0))
        self.assertEqual(lg1,(1.,0.,1.5),'error in loc2glob for (1,0,1.5)')
        
        lg3 = self.cell.loc2glob((0.5,0.0,0.0,0.5))
        self.assertEqual(lg3,(0.,2.5,2.5),'error in loc2glob for (0,2.5,2.5)')
        
        lg6 = self.cell.loc2glob((0.0,0.5,0.0,0.5))
        self.assertEqual(lg6,(1.,2.5,4.),'error in loc2glob for (1,2.5,4)')
        
    def test_interpolate(self):
        r = self.cell2.interpolate((1.,1.,0.),((0.,),(10.,),(12.,),(18.,)))
        self.assertEqual(r,(8.,),'error in interpolate for vertex (1,1,0)')
        
        r = self.cell2.interpolate((1.,1.,1.),((0.,),(10.,),(12.,),(18.,)))
        self.assertEqual(r,(11.,),'error in interpolate for vertex (1,1,1)')
        
        r = self.cell2.interpolate((2.,0.,1.),((0.,),(10.,),(12.,),(18.,)))
        self.assertAlmostEqual(r[0], 9., msg='error in interpolate for vertex (2,0,1)', delta=1.e-5) 
        
        r = self.cell.interpolate((2.,2.,1.),((0.,),(18.,),(20.,),(-5.,)))
        self.assertAlmostEqual(r[0], 8., msg='error in interpolate for vertex (2,0,1)', delta=1.e-5) 
        
    def test_containsPoint(self):
        self.assertEqual(self.cell2.containsPoint((1.,1.,1.)),True,'error in containsPoint for (1,1,1)')
        self.assertEqual(self.cell2.containsPoint((0.,0.,6.)),True,'error in containsPoint for (0,0,6)')
        self.assertEqual(self.cell2.containsPoint((0.,0.,0.)),True,'error in containsPoint for (0,0,0)')
        self.assertEqual(self.cell2.containsPoint((0.,2.,0.)),True,'error in containsPoint for (0,2,0)')
        self.assertEqual(self.cell2.containsPoint((4.,0.,0.)),True,'error in containsPoint for (4,0,0)')
        self.assertEqual(self.cell2.containsPoint((2.,0.,1.)),True,'error in containsPoint for (2,0,1)')
        self.assertEqual(self.cell2.containsPoint((0.,0.,6.01)),False,'error in containsPoint for (0,0,6.01)')
        
    def test_getTransformationJacobian(self):
        self.assertEqual(self.cell2.getTransformationJacobian((1.0,0.0,0.0,0.0)),-48,'error in getTransformationJacobian for cell2')
        self.assertEqual(self.cell.getTransformationJacobian((1.0,0.0,0.0,0.0)),70,'error in getTransformationJacobian for cell')




class Brick_3d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh=mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.,0.)), mkVertex(1,1,(0.,3.,0.)), mkVertex(2,2,(5.,3.,0.)), mkVertex(3,3,(5.,0.,0.)), mkVertex(4,4,(0.,0.,-2.)), mkVertex(5,5,(0.,3.,-2.)), mkVertex(6,6,(5.,3.,-2.)),mkVertex(7,7,(5.,0.,-2.))), [])
        self.cell = cell.Brick_3d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3,4,5,6,7))
        
    def tearDown(self):
        self.mesh = None
        self.cell = None
        
    def test_copy(self):
        c = self.cell.copy()
        self.assertEqual(c.getGeometryType(), cellgeometrytype.CGT_HEXAHEDRON, 'wrong geometry type')
        v = c.getVertices()
        vs= self.cell.getVertices()
        for i in range(8):
            self.assertEqual(v[i].getNumber(),  vs[i].getNumber(), 'wrong label')
        
    def test_getGeometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_HEXAHEDRON, 'wrong geometry type')

    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.,0.))
        self.assertTupleEqual(gc1,(1,(-1.0,-1.0,1.0)),'error in glob2loc for vertex 0 (0,0,0)')
        
        gc2 = self.cell.glob2loc((0.,3.,0.))
        self.assertTupleEqual(gc2,(1,(-1.0,1.0,1.0)),'error in glob2loc for vertex 1 (0,3,0)')
        
        gc3 = self.cell.glob2loc((5.,3.,0.))
        self.assertTupleEqual(gc3,(1,(1.0,1.0,1.0)),'error in glob2loc for vertex 2 (5,3,0)')
        
        gc4 = self.cell.glob2loc((5.,0.,0.))
        self.assertTupleEqual(gc4,(1,(1.0,-1.0,1.0)),'error in glob2loc for vertex 3 (5,0,0)')
        
        gc5 = self.cell.glob2loc((0.,0.,-2.))
        self.assertTupleEqual(gc5,(1,(-1.0,-1.0,-1.0)),'error in glob2loc for vertex 4 (0,0,-2)')
        
        gc6 = self.cell.glob2loc((0.,3.,-2.))
        self.assertTupleEqual(gc6,(1,(-1.0,1.0,-1.0)),'error in glob2loc for vertex 5 (0,3,-2)')
        
        gc7 = self.cell.glob2loc((5.,3.,-2.))
        self.assertTupleEqual(gc7,(1,(1.0,1.0,-1.0)),'error in glob2loc for vertex 6 (5,3,-2)')
        
        gc8 = self.cell.glob2loc((5.,0.,-2.))
        self.assertTupleEqual(gc8,(1,(1.0,-1.0,-1.0)),'error in glob2loc for vertex 7 (5,0,-2)')
        
        #test midside nodes
        gc1 = self.cell.glob2loc((0.,1.5,0.))
        self.assertTupleEqual(gc1,(1,(-1.0,-0.0,1.0)),'error in glob2loc for (0,1.5,0)')
        
        gc2 = self.cell.glob2loc((2.5,3.0,0.))
        self.assertTupleEqual(gc2,(1,(-0.0,1.0,1.0)),'error in glob2loc for (2.5,3,0)')
        
        gc3 = self.cell.glob2loc((5.0,1.5,0.))
        self.assertTupleEqual(gc3,(1,(1.0,0.0,1.0)),'error in glob2loc for (5,1.5,0)')
        
        gc4 = self.cell.glob2loc((2.5,0.,0.))
        self.assertTupleEqual(gc4,(1,(0.0,-1.0,1.0)),'error in glob2loc for (2.5,0,0)')
        
        gc5 = self.cell.glob2loc((0.,1.5,-2.))
        self.assertTupleEqual(gc5,(1,(-1.0,-0.0,-1.0)),'error in glob2loc for (0.,1.5,-2)')
        
        gc6 = self.cell.glob2loc((2.5,3.,-2.))
        self.assertTupleEqual(gc6,(1,(-0.0,1.0,-1.0)),'error in glob2loc for (2.5,3,-2)')
        
        gc7 = self.cell.glob2loc((5.,1.5,-2.))
        self.assertTupleEqual(gc7,(1,(1.0,0.0,-1.0)),'error in glob2loc for (5,1.5,-2)')
        
        gc8 = self.cell.glob2loc((2.5,0.,-2.))
        self.assertTupleEqual(gc8,(1,(0.0,-1.0,-1.0)),'error in glob2loc for (2.5,0,-2)')
        
        #test center
        gc1 = self.cell.glob2loc((2.5,1.5,-1.))
        self.assertTupleEqual(gc1,(1,(0.,0.,0.)),'error in glob2loc for (2.5,1.5,1)')
        
    def test_loc2glob(self): #NameError: global name 'c' is not defined (Cell.py,line 1041)
        #test vertices
        lg1 = self.cell.loc2glob((-1.0,-1.0,1.0))
        self.assertEqual(lg1,(0.,0.,0.),'error in loc2glob for vertex 0 (0,0,0)')
        
        lg3 = self.cell.loc2glob((1.0,1.0, 1.0))
        self.assertEqual(lg3,(5.,3.,0.),'error in loc2glob for vertex 2 (5,3,0)')
        
        #test midside nodes
        lg1 = self.cell.loc2glob((-1.0,-0.0,1.0))
        self.assertEqual(lg1,(0.,1.5,0.),'error in loc2glob for (0,1.5,0)')
        
        lg3 = self.cell.loc2glob((1.0,0.0,1.0))
        self.assertEqual(lg3,(5.0,1.5,0.),'error in loc2glob for (5,1.5,0)')
        
        lg6 = self.cell.loc2glob((-0.0,1.0,-1.0))
        self.assertEqual(lg6,(2.5,3.,-2.),'error in loc2glob for (2.5,3,-2)')
        
    def test_interpolate(self):
        r = self.cell.interpolate((1.,1.,0.),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 8., msg='error in interpolate for (1.1.0)', delta=1.e-5) 
        
        r = self.cell.interpolate((2.5,2.,-1.5),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 22., msg='error in interpolate for (2.5,2,1.5)', delta=1.e-5)
        
        r = self.cell.interpolate((2.5,1.5,-1.),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 18., msg='error in interpolate for (2.5,1.5,-1)', delta=1.e-5)
        
    def test_containsPoint(self):
        self.assertEqual(self.cell.containsPoint((0.,3.,0.)),True,'error in containsPoint for (0,3,0)')
        self.assertEqual(self.cell.containsPoint((5.,3.,-2.)),True,'error in containsPoint for (5,3,-2)')
        self.assertEqual(self.cell.containsPoint((2.5,3.,0.)),True,'error in containsPoint for (2.5,3,0)')
        self.assertEqual(self.cell.containsPoint((0.,0.,0.)),True,'error in containsPoint for (0,0,0)')
        self.assertEqual(self.cell.containsPoint((0.,1.5,-2.)),True,'error in containsPoint for (0,1.5,-2)')
        self.assertEqual(self.cell.containsPoint((2.5,1.5,-1.)),True,'error in containsPoint for (2.5,1.5,-1)')
        self.assertEqual(self.cell.containsPoint((0.,3.01,0.)),False,'error in containsPoint for (0,3.01,0)')
       
        
    def test_getTransformationJacobian(self):
        print(self.cell.getTransformationJacobian((-1.0, 1.0, 1.0)))
        self.assertEqual(self.cell.getTransformationJacobian((-1.0, 1.0, 1.0)), 30.0/8.0, 'error in getTransformationJacobian')
        
# python test_Cell.py for stand-alone test being run
if __name__=='__main__': unittest.main()



#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(Triangle_2d_quad_TestCase('test_geometryType'))
#    suite.addTest(Triangle_2d_quad_TestCase('test_glob2loc'))
#    suite.addTest(Triangle_2d_quad_TestCase('test_loc2glob'))
#    suite.addTest(Triangle_2d_quad_TestCase('test_interpolate'))
#    suite.addTest(Triangle_2d_quad_TestCase('test_containsPoint'))
#    return suite


