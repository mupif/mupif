import math
import numpy as np
import ast
import unittest
import sys
sys.path.append('../..')
from mupif import *
from numpy.testing import assert_array_equal


def mkVertex(number, label, coords): return vertex.Vertex(number=number, label=label, coords=coords)


class Vertex_TestCase(unittest.TestCase):
    def setUp(self):
        self.v21 = mkVertex(1, 1, (0., 0.))
        self.v22 = mkVertex(2, 2, (3., 0.))
        self.v23 = mkVertex(3, 3, (1.5, 4.))
        self.v31 = mkVertex(1, 1, (0., 0., 6.))
        self.v32 = mkVertex(2, 2, (3., 0., 9.))
        self.v33 = mkVertex(3, 3, (1.5, 4., 3.))
    def test_getCoordinates(self):
        # Testing getCoordinates 2D
        assert_array_equal(self.v21.getCoordinates(), (0., 0.))
        assert_array_equal(self.v22.getCoordinates(), (3., 0.))
        assert_array_equal(self.v23.getCoordinates(), (1.5, 4.))
        # Testing getCoordinates 3D
        assert_array_equal(self.v31.getCoordinates(), (0., 0., 6.))
        assert_array_equal(self.v32.getCoordinates(), (3., 0., 9.))
        assert_array_equal(self.v33.getCoordinates(), (1.5, 4., 3.))
    def test_getNumber(self):
        # Testing getNumber 2D
        self.assertEqual(self.v21.getNumber(), 1)
        self.assertEqual(self.v22.getNumber(), 2)
        self.assertEqual(self.v23.getNumber(), 3)
        # Testing getNumber 3D
        self.assertEqual(self.v31.getNumber(), 1)
        self.assertEqual(self.v32.getNumber(), 2)
        self.assertEqual(self.v33.getNumber(), 3)
    def test_getBBox(self):
        # Testing getBBox 2D
        res = self.v21.getBBox()
        self.assertEqual(res.containsPoint((0., 0.)), True)
        self.assertEqual(res.containsPoint((0., 0.001)), False)
        self.assertEqual(res.containsPoint((0.001, 0.)), False)
        
        res = self.v22.getBBox()
        self.assertEqual(res.containsPoint((3., 0.)), True)
        self.assertEqual(res.containsPoint((3., 0.001)), False)
        self.assertEqual(res.containsPoint((3.001, 0.)), False)
        
        res = self.v31.getBBox()
        self.assertEqual(res.containsPoint((0., 0., 6.)), True)
        self.assertEqual(res.containsPoint((0., 0.001, 6.)), False)
        self.assertEqual(res.containsPoint((0.001, 0., 6.)), False)
        self.assertEqual(res.containsPoint((0., 0., 6.001)), False)
        
        res = self.v33.getBBox()
        self.assertEqual(res.containsPoint((1.5, 4., 3.)), True)
        self.assertEqual(res.containsPoint((1.5, 4.001, 3.)), False)
        self.assertEqual(res.containsPoint((1.501, 4., 3.)), False)
        self.assertEqual(res.containsPoint((1.5, 4., 3.001)), False)

    def test_Repr(self):
        res = repr(self.v21)
        vertex = ast.literal_eval(res)
        num = vertex[0]
        label = vertex[1]
        coords = vertex[2]
        assert_array_equal(coords, self.v21.getCoordinates())
        self.assertEqual(num, self.v21.getNumber())


# python test_Vertex.py for stand-alone test being run
if __name__ == '__main__':
    unittest.main()
