import unittest
from mupif import *
import math
import numpy as np


class Triangle_2d_lin_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = Mesh.UnstructuredMesh()
        self.mesh.setup((Vertex.Vertex(0,0,(0.,0.)), Vertex.Vertex(1,1,(2.,0.)), Vertex.Vertex(2,2,(0.,5.))), [])
        self.cell = Cell.Triangle_2d_lin(self.mesh, 0, 1, (0,1,2))

    def tearDown(self):
        self.mesh = None
        self.cell = None

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), CellGeometryType.CGT_TRIANGLE_1, 'wrong geometry type')

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


class Triangle_2d_quad_TestCase(unittest.TestCase):
    def setUp(self):
        self.mesh = Mesh.UnstructuredMesh()
        self.mesh.setup((Vertex.Vertex(0,0,(0.,0.)), Vertex.Vertex(1,1,(2.,0.)), Vertex.Vertex(2,2,(0.,5.)), Vertex.Vertex(3,3,(1.,0.)), Vertex.Vertex(4,4,(1.,2.5)), Vertex.Vertex(5,5,(0.,2.5))), [])
        self.cell = Cell.Triangle_2d_quad(self.mesh, 0, 1, (0,1,2,3,4,5))

    def tearDown(self):
        self.mesh = None
        self.cell = None

    def test_geometryType(self):
        self.assertEqual(self.cell.getGeometryType(), CellGeometryType.CGT_TRIANGLE_2, 'wrong geometry type')

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


