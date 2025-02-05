import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
import numpy as np
import numpy.testing
from numpy.testing import assert_array_equal
def assert_g2l_equal(case,a,b,msg=None):
    case.assertEqual(a[0],b[0])
    assert_array_equal(a[1],b[1])

def mkVertex(number,label,coords): return vertex.Vertex(number=number,label=label,coords=coords)

class Triangle_2d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(0.,5.))), [])
        self.cell = cell.Triangle_2d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2))

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TRIANGLE_1)

    def test_glob2loc(self):
        #test vertices
        assert_array_equal(self.cell.glob2loc((0.,0.)), (1.0, 0.,0.))
        assert_array_equal(self.cell.glob2loc((2.,0.)), (0., 1.,0.))
        assert_array_equal(self.cell.glob2loc((0.,5.)), (0.,0., 1.0))
        #test midside nodes
        assert_array_equal(self.cell.glob2loc((1.,0.)), (0.5, 0.5,0.))
        assert_array_equal(self.cell.glob2loc((1.,2.5)), (0., 0.5,0.5))
        assert_array_equal(self.cell.glob2loc((0.,2.5)), (0.5,0., 0.5))
        #test center
        gc1 = self.cell.glob2loc((2.0/3.0,5.0/3.0))
        self.assertAlmostEqual(gc1[0], 1./3., delta=1.e-5)
        self.assertAlmostEqual(gc1[1], 1./3., delta=1.e-5)
        self.assertAlmostEqual(gc1[2], 1./3., delta=1.e-5)
    def test_loc2glob(self):
        gc = self.cell.loc2glob((0.2, 0.2))
        self.assertAlmostEqual(gc[0], 0.2*2, delta=1.e-5)
        self.assertAlmostEqual(gc[1], 0.6*5, delta=1.e-5)
    def test_interpolate(self):
        r = self.cell.interpolate((1.0,0.0), ((3.0,), (5.0,),(11.,)))
        self.assertAlmostEqual(r[0], 4.0, delta=1.e-5)
        r = self.cell.interpolate((0.0,1.0), ((3.0,), (5.0,), (11.,)))
        self.assertAlmostEqual(r[0], 4./5.*3.0+1./5.*11., delta=1.e-5)
    def test_containsPoint(self):
        self.assertTrue(self.cell.containsPoint((0.1, 0.0)))
        self.assertTrue(self.cell.containsPoint((0., 0.2)))
        self.assertFalse(self.cell.containsPoint((0., 5.1)))

    def test_getTransformationJacobian(self):
        J = self.cell.getTransformationJacobian([])
        self.assertAlmostEqual(J, 10, delta=1.e-8)

    def test_evalN(self):
        lc = (0.5, 0.5)
        N = self.cell._evalN(lc)
        self.assertAlmostEqual(N[0], 0.5, delta=1.e-5)
        self.assertAlmostEqual(N[1], 0.5, delta=1.e-5)
        self.assertAlmostEqual(N[2], 0.0, delta=1.e-5)



class Triangle_2d_quad_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(0.,5.)), mkVertex(3,3,(1.,0.)), mkVertex(4,4,(1.,2.5)), mkVertex(5,5,(0.,2.5))), [])
        self.cell = cell.Triangle_2d_quad(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3,4,5))

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TRIANGLE_2)

    def test_glob2loc(self):
        #test vertices
        assert_array_equal(self.cell.glob2loc((0.,0.)),(1.,0.,0.))
        assert_array_equal(self.cell.glob2loc((2.,0.)),(0.,1.,0.))
        assert_array_equal(self.cell.glob2loc((0.,5.)),(0.,0.,1.))
        #test midside nodes
        assert_array_equal(self.cell.glob2loc((1.,0.)), (0.5, 0.5,0.))
        assert_array_equal(self.cell.glob2loc((1.,2.5)), (0., 0.5,0.5))
        assert_array_equal(self.cell.glob2loc((0.,2.5)), (0.5,0., 0.5))
        #test center
        gc1 = self.cell.glob2loc((2.0/3.0,5.0/3.0))
        np.testing.assert_almost_equal(gc1,(1/3.,1/3.,1/3.))
        #self.assertAlmostEqual(gc1[0], 1./3., delta=1.e-5)
        #self.assertAlmostEqual(gc1[1], 1./3., delta=1.e-5)
        #self.assertAlmostEqual(gc1[2], 1./3., delta=1.e-5)
        
    def test_loc2glob(self):
        gc = self.cell.loc2glob((0.2, 0.2))
        self.assertAlmostEqual(gc[0], 0.2*2, delta=1.e-5)
        self.assertAlmostEqual(gc[1], 0.6*5, delta=1.e-5)
       

    def test_interpolate(self):
        r = self.cell.interpolate((1.0,0.0), ((3.0,),(5.0,), (11.,), (4.0,), (8.0,), (7.0,)))
        self.assertAlmostEqual(r[0], 4.0, delta=1.e-5)
        r = self.cell.interpolate((0.0,1.0), ((3.0,),(5.0,), (11.,), (4.0,), (8.0,), (7.0,)))
        self.assertAlmostEqual(r[0], 4./5.*3.0+1./5.*11., delta=1.e-5)
        
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
        self.assertAlmostEqual(N[0], (2. * l1 - 1.) * l1, delta=1.e-5)
        self.assertAlmostEqual(N[1], (2. * l2 - 1.) * l2, delta=1.e-5)
        self.assertAlmostEqual(N[2], (2. * l3 - 1.) * l3, delta=1.e-5)
        self.assertAlmostEqual(N[3], 4. * l1 * l2, delta=1.e-5)
        self.assertAlmostEqual(N[4], 4. * l2 * l3, delta=1.e-5)
        self.assertAlmostEqual(N[5], 4. * l3 * l1, delta=1.e-5)
        
class Quad_2d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh=mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.)), mkVertex(1,1,(2.,0.)), mkVertex(2,2,(4.,2.)), mkVertex(3,3,(0.,5.))), [])
        self.cell = cell.Quad_2d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3))
    def test_copy(self):
        self.c = self.cell.copy()
        assert_g2l_equal(self,self.c.glob2loc((0.,0.)),(True,(1.0,1.0)))
        assert_g2l_equal(self,self.c.glob2loc((4.,2.)),(True,(-1.0,-1.0)))
        assert_g2l_equal(self,self.c.glob2loc((1.,0.)),(True,(0.,1.)))
        r = self.c.interpolate((2.,2.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],2,delta=1.e-5)
        self.assertEqual(self.c.containsPoint((0.,5.)),True)
        
        
    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_QUAD)
        
    def test_glob2loc(self):
        #test vertices
        assert_g2l_equal(self,self.cell.glob2loc((0.,0.)),(True,(1.0,1.0)))
        gc2 = self.cell.glob2loc((2.,0.))
        self.assertEqual(gc2[0], True)
        self.assertAlmostEqual(gc2[1][0], -1.0, delta=1.e-5)
        self.assertAlmostEqual(gc2[1][1],  1.0, delta=1.e-5)
        assert_g2l_equal(self,self.cell.glob2loc((4.,2.)),(True,(-1.0,-1.0)))
         #test midside nodes
        assert_g2l_equal(self,self.cell.glob2loc((1.,0.)),(True,(0.,1.)))
        assert_g2l_equal(self,self.cell.glob2loc((0.,2.5)),(True,(1.,0.)))
        assert_g2l_equal(self,self.cell.glob2loc((3.,1.)),(True,(-1., 0.)))
        assert_g2l_equal(self,self.cell.glob2loc((2.,3.5)),(True,(0.,-1.)))

    def test_loc2glob(self):
        assert_array_equal(self.cell.loc2glob((0.,1.)),(1.,0.))
        assert_array_equal(self.cell.loc2glob((-1.0,-1.0)),(4.,2.))
    def test_interpolate(self):
        r = self.cell.interpolate((2.,2.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],2,delta=1.e-5)
        
        r = self.cell.interpolate((0.,3.),((0.,),(14.,),(16.,),(-30.,)))
        self.assertAlmostEqual(r[0],-18,delta=1.e-5)
        
    def test_containsPoint(self):
        self.assertEqual(self.cell.containsPoint((2.,2.)),True)
        self.assertEqual(self.cell.containsPoint((0.,-0.2)),False)
        self.assertEqual(self.cell.containsPoint((0.,5.)),True)
        self.assertEqual(self.cell.containsPoint((4.01,2.)),False)
        
    def test_getTransformationJacobian(self):
        self.assertEqual(self.cell.getTransformationJacobian((1.0,1.0)),2.5)
        self.assertEqual(self.cell.getTransformationJacobian((-1.0,-1.0)),3.5)
        self.assertEqual(self.cell.getTransformationJacobian((1.0,-1.0)),5.0)
        self.assertEqual(self.cell.getTransformationJacobian((-1., 0.)),2.25)
        
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
        self.assertEqual(self.r.getGeometryType(), cellgeometrytype.CGT_TETRA)
        assert_array_equal(self.r.glob2loc((0.,0.,0.)),(1.0,0.0,0.0,0.0))
        assert_array_equal(self.r.glob2loc((2.,0.,3.)),(0.0,1.0,0.0,0.0))
        assert_array_equal(self.r.glob2loc((2.,3.5,3.)),(0.0,0.0,0.5,0.5))
        assert_array_equal(self.r.glob2loc((1.,2.5,4.)),(0.0,0.5,0.0,0.5))
        r = self.r.interpolate((2.,2.,1.),((0.,),(18.,),(20.,),(-5.,)))
        self.assertAlmostEqual(r[0], 8., delta=1.e-5)
        
    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_TETRA)
        
    def test_glob2loc(self):
        #test vertices
        gc1 = self.cell.glob2loc((0.,0.,0.))
        assert_array_equal(gc1,(1.0,0.0,0.0,0.0))
        assert_array_equal(self.cell.glob2loc((2.,0.,3.)),(0.0,1.0,0.0,0.0))
        assert_array_equal(self.cell.glob2loc((4.,2.,1.)),(0.0,0.0,1.0,0.0))
        assert_array_equal(self.cell.glob2loc((0.,5.,5.)),(0.0,0.0,0.0,1.0))
        #test midside nodes
        assert_array_equal(self.cell.glob2loc((1.,0.,1.5)),(0.5,0.5,0.0,0.0))
        assert_array_equal(self.cell.glob2loc((2.,1.,0.5)),(0.5,0.0,0.5,0.0))
        assert_array_equal(self.cell.glob2loc((0.,2.5,2.5)),(0.5,0.0,0.0,0.5))
        assert_array_equal(self.cell.glob2loc((3.,1.,2.)),(0.0,0.5,0.5,0.0))
        assert_array_equal(self.cell.glob2loc((2.,3.5,3.)),(0.0,0.0,0.5,0.5))
        assert_array_equal(self.cell.glob2loc((1.,2.5,4.)),(0.0,0.5,0.0,0.5))

        #test center
        gc1 = self.cell2.glob2loc((4.0/3.0,2.0/3.0,6.0/3.0))
        self.assertAlmostEqual(gc1[0], 0, delta=1.e-5)
        self.assertAlmostEqual(gc1[1], 1./3., delta=1.e-5)
        self.assertAlmostEqual(gc1[2], 1./3., delta=1.e-5)
        self.assertAlmostEqual(gc1[3], 1./3., delta=1.e-5)

    def test_loc2glob(self):
        #test vertices
        assert_array_equal(self.cell.loc2glob((1.0,0.0,0.0,0.0)),(0.,0.,0.))
        assert_array_equal(self.cell.loc2glob((0.0,0.0,1.0,0.0)),(4.,2.,1.))
        #test midside nodes
        assert_array_equal(self.cell.loc2glob((0.5,0.5,0.0,0.0)),(1.,0.,1.5))
        assert_array_equal(self.cell.loc2glob((0.5,0.0,0.0,0.5)),(0.,2.5,2.5))
        assert_array_equal(self.cell.loc2glob((0.0,0.5,0.0,0.5)),(1.,2.5,4.))

    def test_interpolate(self):
        assert_array_equal(self.cell2.interpolate((1.,1.,0.),((0.,),(10.,),(12.,),(18.,))),(8.,))
        assert_array_equal(self.cell2.interpolate((1.,1.,1.),((0.,),(10.,),(12.,),(18.,))),(11.,))
        r = self.cell2.interpolate((2.,0.,1.),((0.,),(10.,),(12.,),(18.,)))
        self.assertAlmostEqual(r[0], 9., delta=1.e-5)
        r = self.cell.interpolate((2.,2.,1.),((0.,),(18.,),(20.,),(-5.,)))
        self.assertAlmostEqual(r[0], 8., delta=1.e-5)

    def test_containsPoint(self):
        self.assertEqual(self.cell2.containsPoint((1.,1.,1.)),True)
        self.assertEqual(self.cell2.containsPoint((0.,0.,6.)),True)
        self.assertEqual(self.cell2.containsPoint((0.,0.,0.)),True)
        self.assertEqual(self.cell2.containsPoint((0.,2.,0.)),True)
        self.assertEqual(self.cell2.containsPoint((4.,0.,0.)),True)
        self.assertEqual(self.cell2.containsPoint((2.,0.,1.)),True)
        self.assertEqual(self.cell2.containsPoint((0.,0.,6.01)),False)
        
    def test_getTransformationJacobian(self):
        self.assertEqual(self.cell2.getTransformationJacobian((1.0,0.0,0.0,0.0)),-48)
        self.assertEqual(self.cell.getTransformationJacobian((1.0,0.0,0.0,0.0)),70)




class Brick_3d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh=mesh.UnstructuredMesh()
        self.mesh.setup((mkVertex(0,0,(0.,0.,0.)), mkVertex(1,1,(0.,3.,0.)), mkVertex(2,2,(5.,3.,0.)), mkVertex(3,3,(5.,0.,0.)), mkVertex(4,4,(0.,0.,-2.)), mkVertex(5,5,(0.,3.,-2.)), mkVertex(6,6,(5.,3.,-2.)),mkVertex(7,7,(5.,0.,-2.))), [])
        self.cell = cell.Brick_3d_lin(mesh=self.mesh, number=0, label=1, vertices=(0,1,2,3,4,5,6,7))
        
    def test_copy(self):
        c = self.cell.copy()
        self.assertEqual(c.getGeometryType(), cellgeometrytype.CGT_HEXAHEDRON)
        v = c.getVertices()
        vs= self.cell.getVertices()
        for i in range(8):
            self.assertEqual(v[i].getNumber(),  vs[i].getNumber())
        
    def test_getGeometryType(self):
        self.assertEqual(self.cell.getGeometryType(), cellgeometrytype.CGT_HEXAHEDRON)

    def test_glob2loc(self):
        #test vertices
        assert_g2l_equal(self,self.cell.glob2loc((0.,0.,0.)),(1,(-1.0,-1.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((0.,3.,0.)),(1,(-1.0,1.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.,3.,0.)),(1,(1.0,1.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.,0.,0.)),(1,(1.0,-1.0,1.0)),)
        assert_g2l_equal(self,self.cell.glob2loc((0.,0.,-2.)),(1,(-1.0,-1.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((0.,3.,-2.)),(1,(-1.0,1.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.,3.,-2.)),(1,(1.0,1.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.,0.,-2.)),(1,(1.0,-1.0,-1.0)))
        #test midside nodes
        assert_g2l_equal(self,self.cell.glob2loc((0.,1.5,0.)),(1,(-1.0,-0.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((2.5,3.0,0.)),(1,(-0.0,1.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.0,1.5,0.)),(1,(1.0,0.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((2.5,0.,0.)),(1,(0.0,-1.0,1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((0.,1.5,-2.)),(1,(-1.0,-0.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((2.5,3.,-2.)),(1,(-0.0,1.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((5.,1.5,-2.)),(1,(1.0,0.0,-1.0)))
        assert_g2l_equal(self,self.cell.glob2loc((2.5,0.,-2.)),(1,(0.0,-1.0,-1.0)))
        #test center
        gc1 = self.cell.glob2loc((2.5,1.5,-1.))
        assert_g2l_equal(self,gc1,(1,(0.,0.,0.)))
        
    def test_loc2glob(self): #NameError: global name 'c' is not defined (Cell.py,line 1041)
        #test vertices
        lg1 = self.cell.loc2glob((-1.0,-1.0,1.0))
        assert_array_equal(lg1,(0.,0.,0.))
        
        lg3 = self.cell.loc2glob((1.0,1.0, 1.0))
        assert_array_equal(lg3,(5.,3.,0.))
        
        #test midside nodes
        lg1 = self.cell.loc2glob((-1.0,-0.0,1.0))
        assert_array_equal(lg1,(0.,1.5,0.))
        
        lg3 = self.cell.loc2glob((1.0,0.0,1.0))
        assert_array_equal(lg3,(5.0,1.5,0.))
        
        lg6 = self.cell.loc2glob((-0.0,1.0,-1.0))
        assert_array_equal(lg6,(2.5,3.,-2.))
        
    def test_interpolate(self):
        r = self.cell.interpolate((1.,1.,0.),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 8., delta=1.e-5)
        
        r = self.cell.interpolate((2.5,2.,-1.5),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 22., delta=1.e-5)
        
        r = self.cell.interpolate((2.5,1.5,-1.),[(0.,),(15.,),(30.,),(15.,),(6.,),(21.,),(36.,),(21.,)])
        self.assertAlmostEqual(r[0], 18., delta=1.e-5)
        
    def test_containsPoint(self):
        self.assertEqual(self.cell.containsPoint((0.,3.,0.)),True)
        self.assertEqual(self.cell.containsPoint((5.,3.,-2.)),True)
        self.assertEqual(self.cell.containsPoint((2.5,3.,0.)),True)
        self.assertEqual(self.cell.containsPoint((0.,0.,0.)),True)
        self.assertEqual(self.cell.containsPoint((0.,1.5,-2.)),True)
        self.assertEqual(self.cell.containsPoint((2.5,1.5,-1.)),True)
        self.assertEqual(self.cell.containsPoint((0.,3.01,0.)),False)
       
        
    def test_getTransformationJacobian(self):
        print(self.cell.getTransformationJacobian((-1.0, 1.0, 1.0)))
        self.assertEqual(self.cell.getTransformationJacobian((-1.0, 1.0, 1.0)), 30.0/8.0)

# python test_Cell.py for stand-alone test being run
if __name__=='__main__': unittest.main()
