import sys
sys.path.append('../..')

import unittest
from mupif import *
import math


class BBox_TestCase(unittest.TestCase):
    def setUp(self):
        #rectangles
        self.b21 = bbox.BBox((0.,0.), (3., 3.))
        self.b22 = bbox.BBox((3.,3.), (8., 6.))
        self.b23 = bbox.BBox((1.5,1.5), (3.5, 5.))
        self.b24 = bbox.BBox((13.,2.), (18.,5.))
        
        #blocks
        self.b31 = bbox.BBox((0.,0.,0.), (3., 3.,2.))
        self.b32 = bbox.BBox((3.,3.,2.), (8., 6.,5.))
        self.b33 = bbox.BBox((1.5,1.5,1.5), (3.5, 5.,4.))
        self.b34 = bbox.BBox((0.,0.,5.5), (8.,6.,10.))
         
# Testing containsPoint rectangle b21    
    def test_containsPoint(self):
        self.assertTrue(self.b21.containsPoint((1.,1.)))
        self.assertTrue(self.b21.containsPoint((0.,0.)))
        self.assertTrue(self.b21.containsPoint((3.,1.)))
        self.assertTrue(self.b21.containsPoint((3.,3.)))
        self.assertTrue(self.b22.containsPoint((3.,3.)))
        self.assertTrue(self.b23.containsPoint((3.,3.)))
        self.assertFalse(self.b21.containsPoint((6.,6.)))
        self.assertTrue(self.b22.containsPoint((6.,6.)))
        self.assertFalse(self.b23.containsPoint((6.,6.)))
        self.assertFalse(self.b21.containsPoint((8.,6.)))
        self.assertTrue(self.b22.containsPoint((8.,6.)))
        self.assertFalse(self.b23.containsPoint((8.,6.)))
        self.assertFalse(self.b21.containsPoint((3.5,5.)))
        self.assertTrue(self.b22.containsPoint((3.5,5.)))
        self.assertTrue(self.b23.containsPoint((3.5,5.)))
        self.assertTrue(self.b31.containsPoint((3.,3.,2.)))
        self.assertTrue(self.b32.containsPoint((3.,3.,2.)))
        self.assertTrue(self.b33.containsPoint((3.,3.,2.)))
        self.assertTrue(self.b31.containsPoint((3.,3.,1.)))
        self.assertFalse(self.b32.containsPoint((3.,3.,1.)))
        self.assertFalse(self.b33.containsPoint((3.,3.,1.)))
        self.assertFalse(self.b31.containsPoint((3.,3.,8.)))
        self.assertFalse(self.b32.containsPoint((3.,3.,8.)))
        self.assertFalse(self.b33.containsPoint((3.,3.,8.)))
        self.assertFalse(self.b31.containsPoint((3.5,5.,4.)))
        self.assertTrue(self.b32.containsPoint((3.5,5.,4.)))
        self.assertTrue(self.b33.containsPoint((3.5,5.,4.)))
        
    def test_intersects(self):
         # Testing intersects combinations rectangels b21, b22, b23, b24
        self.assertTrue(self.b21.intersects((self.b23)))
        self.assertTrue(self.b23.intersects((self.b21)))
        self.assertTrue(self.b21.intersects((self.b22)))
        self.assertTrue(self.b22.intersects((self.b23)))
        self.assertFalse(self.b22.intersects((self.b24)))
        # Testing intersects combinations blocks b31, b32, b33, b34
        self.assertTrue(self.b31.intersects((self.b33)))
        self.assertTrue(self.b33.intersects((self.b31)))
        self.assertTrue(self.b31.intersects((self.b32)))
        self.assertTrue(self.b32.intersects((self.b33)))
        self.assertFalse(self.b32.intersects((self.b34)))
        
    def test_merge_2d(self):
        # Testing merge 2D
        self.b21.merge(self.b23)
        self.assertTrue(self.b21.containsPoint((0.,0.)))
        self.assertTrue(self.b21.containsPoint((3.5,5.)))
        self.assertTrue(self.b21.containsPoint((1.,4.)))
        self.assertFalse(self.b21.containsPoint((5.,3.)))

        self.b22.merge(self.b21) 
        self.assertTrue(self.b22.containsPoint((0.,0.)))
        self.assertTrue(self.b22.containsPoint((8.,6.)))
        self.assertTrue(self.b22.containsPoint((1.5,5.)))
        self.assertFalse(self.b21.containsPoint((5.,2.)))

    def test_merge_2d_coords(self):
        # Testing merge 2D (coordinates)
        self.b21.merge((3.5,5.))
        self.assertTrue(self.b21.containsPoint((0.,0.)))
        self.assertTrue(self.b21.containsPoint((3.5,5.)))
        self.assertTrue(self.b21.containsPoint((1.,4.)))
        self.assertFalse(self.b21.containsPoint((5.,3.)))
        
        self.b22.merge((0.,0.))
        self.assertTrue(self.b22.containsPoint((0.,0.)))
        self.assertTrue(self.b22.containsPoint((8.,6.)))
        self.assertTrue(self.b22.containsPoint((1.5,5.)))
        self.assertFalse(self.b21.containsPoint((5.,2.)))
        
    def test_merge_3d(self):
        # Testing merge 3D (BBox)
        self.b31.merge(self.b33) 
        self.assertTrue(self.b31.containsPoint((0.,0.,0.)))
        self.assertTrue(self.b31.containsPoint((3.5,5.,4.)))
        self.assertTrue(self.b31.containsPoint((1.,4.,3.)))
        self.assertFalse(self.b31.containsPoint((5.,3.,3.)))
        
        self.b32.merge(self.b31) 
        self.assertTrue(self.b32.containsPoint((0.,0.,0.)))
        self.assertTrue(self.b32.containsPoint((8.,6.,5.)))
        self.assertTrue(self.b32.containsPoint((1.,4.,3.)))
        self.assertTrue(self.b32.containsPoint((5.,3.,3.)))
        self.assertFalse(self.b32.containsPoint((5.,3.,8.)))
        
    def test_merge_3d_coords(self):
        # Testing merge 3D (coordinates)
        self.b31.merge((3.5,5.,4))
        self.assertTrue(self.b31.containsPoint((0.,0.,0.)))
        self.assertTrue(self.b31.containsPoint((3.5,5.,4.)))
        self.assertTrue(self.b31.containsPoint((1.,4.,3.)))
        self.assertFalse(self.b31.containsPoint((5.,3.,3.)))
        
        self.b32.merge((0.,0.,0.))
        self.assertTrue(self.b32.containsPoint((0.,0.,0.)))
        self.assertTrue(self.b32.containsPoint((8.,6.,5.)))
        self.assertTrue(self.b32.containsPoint((1.,4.,3.)))
        self.assertTrue(self.b32.containsPoint((5.,3.,3.)))
        self.assertFalse(self.b32.containsPoint((5.,3.,8.)))
    
      
# python test_Cell.py for stand-alone test being run
if __name__=='__main__': unittest.main()


