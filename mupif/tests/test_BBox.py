import sys
sys.path.append('../..')

import unittest
from mupif import *
import math


class BBox_TestCase(unittest.TestCase):
    def setUp(self):
        #rectangles
        self.b21 = BBox.BBox((0.,0.), (3., 3.))
        self.b22 = BBox.BBox((3.,3.), (8., 6.))
        self.b23 = BBox.BBox((1.5,1.5), (3.5, 5.))
        self.b24 = BBox.BBox((13.,2.), (18.,5.))
        
        #blocks
        self.b31 = BBox.BBox((0.,0.,0.), (3., 3.,2.))
        self.b32 = BBox.BBox((3.,3.,2.), (8., 6.,5.))
        self.b33 = BBox.BBox((1.5,1.5,1.5), (3.5, 5.,4.))
        self.b34 = BBox.BBox((0.,0.,5.5), (8.,6.,10.))
         
    def tearDown(self):
        self.b21 = None
        self.b22 = None
        self.b23 = None
        self.b24 = None

        self.b31 = None
        self.b32 = None
        self.b33 = None
        self.b34 = None
         
# Testing containsPoint rectangle b21    
    def test_containsPoint(self):
        res = self.b21.containsPoint((1.,1.))
        self.assertEqual(res, True, 'error in containsPoint for b21(1,1)')
        
    def test_containsPoint(self):
        res = self.b21.containsPoint((0.,0.))
        self.assertEqual(res, True, 'error in containsPoint for b21(0,0)')
        
    def test_containsPoint(self):
        res = self.b21.containsPoint((3.,1.))
        self.assertEqual(res, True, 'error in containsPoint for b21(3,1)')
        
# Testing containsPoint combinations rectangles b21, b22 and b23
    def test_containsPoint(self):
        res = self.b21.containsPoint((3.,3.))
        self.assertEqual(res, True, 'error in containsPoint for b21(3,3)')
        
    def test_containsPoint(self):
        res = self.b22.containsPoint((3.,3.))
        self.assertEqual(res, True, 'error in containsPoint for b22(3,3)')
        
    def test_containsPoint(self):
        res = self.b23.containsPoint((3.,3.))
        self.assertEqual(res, True, 'error in containsPoint for b23(3,3)')
        
    def test_containsPoint(self):
        res = self.b21.containsPoint((6.,6.))
        self.assertEqual(res, False, 'error in containsPoint for b21(6,6)')
        
    def test_containsPoint(self):
        res = self.b22.containsPoint((6.,6.))
        self.assertEqual(res, True, 'error in containsPoint for b22(6,6)')
        
    def test_containsPoint(self):
        res = self.b23.containsPoint((6.,6.))
        self.assertEqual(res, False, 'error in containsPoint for b23(6,6)')
        
    def test_containsPoint(self):
        res = self.b21.containsPoint((8.,6.))
        self.assertEqual(res, False, 'error in containsPoint for b21(8,6)')
        
    def test_containsPoint(self):
        res = self.b22.containsPoint((8.,6.))
        self.assertEqual(res, True, 'error in containsPoint for b22(8,6)')

    def test_containsPoint(self):
        res = self.b23.containsPoint((8.,6.))
        self.assertEqual(res, False, 'error in containsPoint for b23(8,6)')
        
    def test_containsPoint(self):
        res = self.b21.containsPoint((3.5,5.))
        self.assertEqual(res, False, 'error in containsPoint for b21(3.5,5)')
        
    def test_containsPoint(self):
        res = self.b22.containsPoint((3.5,5.))
        self.assertEqual(res, True, 'error in containsPoint for b22(3.5,5)')

    def test_containsPoint(self):
        res = self.b23.containsPoint((3.5,5.))
        self.assertEqual(res, True, 'error in containsPoint for b23(3.5,5)')
        
# Testing containsPoint combinations blocks b31, b32 and b33
    def test_containsPoint(self):
        res = self.b31.containsPoint((3.,3.,2.))
        self.assertEqual(res, True, 'error in containsPoint for b31(3,3,2)')
        
    def test_containsPoint(self):
        res = self.b32.containsPoint((3.,3.,2.))
        self.assertEqual(res, True, 'error in containsPoint for b32(3,3,2)')
        
    def test_containsPoint(self):
        res = self.b33.containsPoint((3.,3.,2.))
        self.assertEqual(res, True, 'error in containsPoint for b33(3,3,2)')

    def test_containsPoint(self):
        res = self.b31.containsPoint((3.,3.,1.))
        self.assertEqual(res, True, 'error in containsPoint for b31(3,3,1)')
        
    def test_containsPoint(self):
        res = self.b32.containsPoint((3.,3.,1.))
        self.assertEqual(res, False, 'error in containsPoint for b32(3,3,1)')
        
    def test_containsPoint(self):
        res = self.b33.containsPoint((3.,3.,1.))
        self.assertEqual(res, False, 'error in containsPoint for b33(3,3,1)')
        
    def test_containsPoint(self):
        res = self.b31.containsPoint((3.,3.,8.))
        self.assertEqual(res, False, 'error in containsPoint for b31(3,3,8)')
        
    def test_containsPoint(self):
        res = self.b32.containsPoint((3.,3.,8.))
        self.assertEqual(res, False, 'error in containsPoint for b32(3,3,8)')
        
    def test_containsPoint(self):
        res = self.b33.containsPoint((3.,3.,8.))
        self.assertEqual(res, False, 'error in containsPoint for b33(3,3,8)')    
        
    def test_containsPoint(self):
        res = self.b31.containsPoint((3.5,5.,4.))
        self.assertEqual(res, False, 'error in containsPoint for b31(3.5,5,4)')
        
    def test_containsPoint(self):
        res = self.b32.containsPoint((3.5,5.,4.))
        self.assertEqual(res, True, 'error in containsPoint for b32(3.5,5,4)')
        
    def test_containsPoint(self):
        res = self.b33.containsPoint((3.5,5.,4.))
        self.assertEqual(res, True, 'error in containsPoint for b33(3.5,5,4)')
        
 # Testing intersects combinations rectangels b21, b22, b23, b24
    def test_intersects(self):
        res = self.b21.intersects((self.b23))
        self.assertEqual(res, True, 'error in intersects for b21 and b23')
        
    def test_intersects(self):
        res = self.b23.intersects((self.b21))
        self.assertEqual(res, True, 'error in intersects for b23 and b21')
        
    def test_intersects(self):
        res = self.b21.intersects((self.b22))
        self.assertEqual(res, True, 'error in intersects for b21 and b22')
        
    def test_intersects(self):
        res = self.b22.intersects((self.b23))
        self.assertEqual(res, True, 'error in intersects for b22 and b23')

    def test_intersects(self):
        res = self.b22.intersects((self.b24))
        self.assertEqual(res, False, 'error in intersects for b22 and b24')
        
# Testing intersects combinations blocks b31, b32, b33, b34
    def test_intersects(self):
        res = self.b31.intersects((self.b33))
        self.assertEqual(res, True, 'error in intersects for b31 and b33')
        
    def test_intersects(self):
        res = self.b33.intersects((self.b31))
        self.assertEqual(res, True, 'error in intersects for b33 and b31')
        
    def test_intersects(self):
        res = self.b31.intersects((self.b32))
        self.assertEqual(res, True, 'error in intersects for b31 and b32')
        
    def test_intersects(self):
        res = self.b32.intersects((self.b33))
        self.assertEqual(res, True, 'error in intersects for b32 and b33')

    def test_intersects(self):
        res = self.b32.intersects((self.b34))
        self.assertEqual(res, False, 'error in intersects for b32 and b34')
        
# Testing merge 2D
    def test_merge(self):
        self.b21.merge(self.b23)
        res = self.b21.containsPoint((0.,0.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(0,0)')
        res = self.b21.containsPoint((3.5,5.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(3.5,5)')
        res = self.b21.containsPoint((1.,4.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(1,4)')
        res = self.b21.containsPoint((5.,3.))
        self.assertEqual(res, False, 'error in merge for b21 and b23(5,3)')
        
    def test_merge(self):
        self.b22.merge(self.b21) 
        res = self.b22.containsPoint((0.,0.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(0,0)')
        res = self.b22.containsPoint((8.,6.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(8,6)')
        res = self.b22.containsPoint((1.5,5.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(1.5,5)')
        res = self.b21.containsPoint((5.,2.))
        self.assertEqual(res, False, 'error in merge for b22 and b21(5,2)')
        
# Testing merge 3D (BBox)
    def test_merge(self):
        self.b31.merge(self.b33) 
        res = self.b31.containsPoint((0.,0.,0.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(0,0,0)')
        res = self.b31.containsPoint((3.5,5.,4.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(3.5,5,4)')
        res = self.b31.containsPoint((1.,4.,3.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(1,4,3)')
        res = self.b31.containsPoint((5.,3.,3.))
        self.assertEqual(res, False, 'error in merge for b31 and b33(5,3,3)')
        
    def test_merge(self):
        self.b32.merge(self.b31) 
        res = self.b32.containsPoint((0.,0.,0.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(0,0,0)')
        res = self.b32.containsPoint((8.,6.,5.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(8,6,5)')
        res = self.b32.containsPoint((1.,4.,3.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(1,4,3)')
        res = self.b32.containsPoint((5.,3.,3.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(5,3,3)')
        res = self.b32.containsPoint((5.,3.,8.))
        self.assertEqual(res, False, 'error in merge for b32 and b31(5,3,8)')
        
# Testing merge 2D (coordinates)
    def test_merge(self):
        self.b21.merge((3.5,5.))
        res = self.b21.containsPoint((0.,0.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(0,0)')
        res = self.b21.containsPoint((3.5,5.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(3.5,5)')
        res = self.b21.containsPoint((1.,4.))
        self.assertEqual(res, True, 'error in merge for b21 and b23(1,4)')
        res = self.b21.containsPoint((5.,3.))
        self.assertEqual(res, False, 'error in merge for b21 and b23(5,3)')
        
    def test_merge(self):
        self.b22.merge((0.,0.))
        res = self.b22.containsPoint((0.,0.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(0,0)')
        res = self.b22.containsPoint((8.,6.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(8,6)')
        res = self.b22.containsPoint((1.5,5.))
        self.assertEqual(res, True, 'error in merge for b22 and b21(1.5,5)')
        res = self.b21.containsPoint((5.,2.))
        self.assertEqual(res, False, 'error in merge for b22 and b21(5,2)')
        
# Testing merge 3D (coordinates)
    def test_merge(self):
        self.b31.merge((3.5,5.,4))
        res = self.b31.containsPoint((0.,0.,0.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(0,0,0)')
        res = self.b31.containsPoint((3.5,5.,4.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(3.5,5,4)')
        res = self.b31.containsPoint((1.,4.,3.))
        self.assertEqual(res, True, 'error in merge for b31 and b33(1,4,3)')
        res = self.b31.containsPoint((5.,3.,3.))
        self.assertEqual(res, False, 'error in merge for b31 and b33(5,3,3)')
        
    def test_merge(self):
        self.b32.merge((0.,0.,0.))
        res = self.b32.containsPoint((0.,0.,0.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(0,0,0)')
        res = self.b32.containsPoint((8.,6.,5.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(8,6,5)')
        res = self.b32.containsPoint((1.,4.,3.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(1,4,3)')
        res = self.b32.containsPoint((5.,3.,3.))
        self.assertEqual(res, True, 'error in merge for b32 and b31(5,3,3)')
        res = self.b32.containsPoint((5.,3.,8.))
        self.assertEqual(res, False, 'error in merge for b32 and b31(5,3,8)')        
    
      
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


