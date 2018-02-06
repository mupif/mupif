import sys
sys.path.append('../..')

import unittest
from mupif import *
import math


class GaussIntegrationRule_TestCase(unittest.TestCase):        
# Testing getIntegrationPoints
    def test_getIntegrationPoints(self):
        ### test Trangle with
        rule = IntegrationRule.GaussIntegrationRule()
        cgt = CellGeometryType.CGT_TRIANGLE_1
        #one integration point
        self.assertTrue(rule.getIntegrationPoints(cgt,1) == [((0.333333333333, 0.333333333333), 0.5)])
        # three integration point
        self.assertTrue(rule.getIntegrationPoints(cgt,3) == [((0.166666666666667, 0.166666666666667),  0.166666666666667),
                              ((0.666666666666667, 0.166666666666667),  0.166666666666667),
                              ((0.166666666666667, 0.666666666666667),  0.166666666666667)])
        # four integration point
        self.assertTrue(rule.getIntegrationPoints(cgt,4) == [((0.333333333333333, 0.333333333333333), -0.281250000000000),
                               ((0.200000000000000, 0.600000000000000),  0.260416666666667),
                               ((0.200000000000000, 0.200000000000000),  0.260416666666667),
                               ((0.600000000000000, 0.200000000000000),  0.260416666666667)])
        ### test Quad
        cgt = CellGeometryType.CGT_QUAD
        #one integration point
        self.assertTrue(rule.getIntegrationPoints(cgt,1) == [((0.0, 0.0), 4.0)])
        #one integration point
        self.assertTrue(rule.getIntegrationPoints(cgt,4) == [(( 0.577350269189626,  0.577350269189626), 1),
                               ((-0.577350269189626,  0.577350269189626), 1),
                               ((-0.577350269189626, -0.577350269189626), 1),
                               (( 0.577350269189626, -0.577350269189626), 1)])
    def test_getRequiredNumberOfPoints(self):
        rule = IntegrationRule.GaussIntegrationRule()
        cgt = CellGeometryType.CGT_TRIANGLE_1
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 0) == 1)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 1) == 1)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 2) == 3)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 3) == 4)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 4) == -1)
        
        cgt = CellGeometryType.CGT_QUAD
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 0) == 4)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 1) == 4)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 2) == 4)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 3) == 4)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 4) == 5)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 5) == 6)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 6) == 7)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 7) == 8)
        self.assertTrue(rule.getRequiredNumberOfPoints(cgt, 8) == -1)
        
# python test_Cell.py for stand-alone test being run
if __name__=='__main__': unittest.main()


