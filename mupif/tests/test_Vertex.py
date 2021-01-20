import unittest,sys
sys.path.append('../..')
from mupif import *
import math
import numpy as np
import ast

class Vertex_TestCase(unittest.TestCase):
    def setUp(self):
        
        self.v21=vertex.Vertex(1,1,(0.,0.))
        self.v22=vertex.Vertex(2,2,(3.,0.))
        self.v23=vertex.Vertex(3,3,(1.5,4.))        
        
        self.v31=vertex.Vertex(1,1,(0.,0.,6.))
        self.v32=vertex.Vertex(2,2,(3.,0.,9.))
        self.v33=vertex.Vertex(3,3,(1.5,4.,3.)) 
        
    def tearDown(self):
        
        self.v21=None
        self.v22=None
        self.v23=None
        
        self.v31=None
        self.v32=None
        self.v33=None
        
# Testing getCoordinates 2D        
    def test_getCoordinates(self):
        res=self.v21.getCoordinates()
        self.assertEqual(res,(0.,0.),'error in getCoordinates for v21')
    
        res=self.v22.getCoordinates()
        self.assertEqual(res,(3.,0.),'error in getCoordinates for v22')
        
        res=self.v23.getCoordinates()
        self.assertEqual(res,(1.5,4.),'error in getCoordinates for v23')
        
# Testing getCoordinates 3D         
        res=self.v31.getCoordinates()
        self.assertEqual(res,(0.,0.,6.),'error in getCoordinates for v31')
    
        res=self.v32.getCoordinates()
        self.assertEqual(res,(3.,0.,9.),'error in getCoordinates for v32')
        
        res=self.v33.getCoordinates()
        self.assertEqual(res,(1.5,4.,3.),'error in getCoordinates for v33')
        
# Testing getNumber 2D        
    def test_getNumber(self):
        res=self.v21.getNumber()
        self.assertEqual(res,1,'error in getNumber for v21')
    
        res=self.v22.getNumber()
        self.assertEqual(res,2,'error in getNumber for v22')
        
        res=self.v23.getNumber()
        self.assertEqual(res,3,'error in getNumber for v23')
        
# Testing getNumber 3D         
        res=self.v31.getNumber()
        self.assertEqual(res,1,'error in getNumber for v31')
    
        res=self.v32.getNumber()
        self.assertEqual(res,2,'error in getNumber for v32')
        
        res=self.v33.getNumber()
        self.assertEqual(res,3,'error in getNumber for v33')
# Testing getBBox 2D 
    def test_getBBox(self):
        res=self.v21.getBBox()
        self.assertEqual(res.containsPoint ((0.,0.)), True, 'error in getBBox for v21')
        self.assertEqual(res.containsPoint ((0.,0.001)), False, 'error in getBBox for v21')
        self.assertEqual(res.containsPoint ((0.001,0.)), False, 'error in getBBox for v21')
        
        res=self.v22.getBBox()
        self.assertEqual(res.containsPoint ((3.,0.)), True, 'error in getBBox for v22')
        self.assertEqual(res.containsPoint ((3.,0.001)), False, 'error in getBBox for v22')
        self.assertEqual(res.containsPoint ((3.001,0.)), False, 'error in getBBox for v22')
        
        res=self.v31.getBBox()
        self.assertEqual(res.containsPoint ((0.,0.,6.)), True, 'error in getBBox for v31')
        self.assertEqual(res.containsPoint ((0.,0.001,6.)), False, 'error in getBBox for v31')
        self.assertEqual(res.containsPoint ((0.001,0.,6.)), False, 'error in getBBox for v31')
        self.assertEqual(res.containsPoint ((0.,0.,6.001)), False, 'error in getBBox for v31')
        
        res=self.v33.getBBox()
        self.assertEqual(res.containsPoint ((1.5,4.,3.)), True, 'error in getBBox for v33')
        self.assertEqual(res.containsPoint ((1.5,4.001,3.)), False, 'error in getBBox for v33')
        self.assertEqual(res.containsPoint ((1.501,4.,3.)), False, 'error in getBBox for v33')
        self.assertEqual(res.containsPoint ((1.5,4.,3.001)), False, 'error in getBBox for v33')

    def test_Repr(self):
        res = repr(self.v21)
        vertex = ast.literal_eval(res)
        num = vertex[0]
        label = vertex[1]
        coords = vertex[2]
        self.assertEqual(coords, self.v21.getCoordinates(), 'error in getCoordinates __repr__')
        self.assertEqual(num, self.v21.getNumber(), 'error in getCoordinates __repr__')


# python test_Vertex.py for stand-alone test being run
if __name__=='__main__': unittest.main()


