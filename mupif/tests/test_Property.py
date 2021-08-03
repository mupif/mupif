import unittest,sys
sys.path.append('../..')

from mupif import *
import math
import tempfile
import mupif as mp
import numpy as np

class Property_TestCase(unittest.TestCase):
    def setUp(self):

        self.t1 = 6*mp.U.s
        self.t2 = 15*mp.U.s
        self.t3 = 9*mp.U.s

        
        self.p1=property.ConstantProperty(value=16.,propID=PropertyID.PID_Concentration,valueType=ValueType.Scalar,unit=mp.U['m'],time=self.t1,objectID=1)
        self.p2=property.ConstantProperty(value=7.,propID=PropertyID.PID_Velocity,valueType=ValueType.Vector,unit=mp.U['m/s'],time=self.t2,objectID=16)
        self.p3=property.ConstantProperty(value=9.,propID=PropertyID.PID_ParticleSigma,valueType=ValueType.Tensor,unit=mp.U['kg/(m*s**2)'],time=self.t3, objectID=8)

    def test_getValue(self):
        res=self.p1.getValue(6*mp.U.s)
        self.assertEqual(res,16.)
        self.assertEqual(self.p1.getQuantity(6*mp.U.s),16.*mp.U.m)
        
        res=self.p2.getValue(self.t2)
        self.assertEqual(res,7.)  
        
        res=self.p3.getValue(self.t3)
        self.assertEqual(res,9.)
        
    def test_getValueType(self):
        self.assertEqual(self.p1.getValueType(),ValueType.Scalar)
        self.assertEqual(self.p2.getValueType(),ValueType.Vector)
        self.assertEqual(self.p3.getValueType(),ValueType.Tensor)
        
    def test_getTime(self):
        self.assertEqual(self.p1.getTime().inUnitsOf('s').getValue(),6)
        self.assertEqual(self.p2.getTime().inUnitsOf('s').getValue(),15)        
        self.assertEqual(self.p3.getTime().inUnitsOf('s').getValue(),9)  
        
    def test_getPropertyID(self):
        self.assertEqual(self.p1.getPropertyID(),PropertyID.PID_Concentration)
        self.assertEqual(self.p2.getPropertyID(),PropertyID.PID_Velocity)
        self.assertEqual(self.p3.getPropertyID(),PropertyID.PID_ParticleSigma)
        
    def test_getObjectID(self):
        self.assertEqual(self.p1.getObjectID(),1)
        self.assertEqual(self.p2.getObjectID(),16)
        self.assertEqual(self.p3.getObjectID(),8)
        
    def test_getUnit(self):
        self.assertTrue(self.p1.getUnit().isCompatible(mp.U['m']))
        self.assertTrue(self.p2.getUnit().isCompatible(mp.U['m/s']))
        self.assertTrue(self.p3.getUnit().isCompatible(mp.U['kg/(m*s**2)']))
        
    def test_dumpToLocalFile(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.res=None
            self.p1.dumpToLocalFile(tmp+'/dumpfile')
            self.res=property.ConstantProperty.loadFromLocalFile(tmp+'/dumpfile')
            self.assertEqual(self.res.getValue(self.t1),16.)
            self.assertEqual(self.res.getValueType(),ValueType.Scalar)
            self.assertEqual(self.res.getTime(),6*mp.U.s)
            self.assertEqual(self.res.getPropertyID(),PropertyID.PID_Concentration)
            self.assertEqual(self.res.getObjectID(),1)
            self.assertTrue(self.res.getUnit().isCompatible(mp.U['m']))
            
            self.res=None
            self.p3.dumpToLocalFile(tmp+'/dumpfile2')
            self.res=property.ConstantProperty.loadFromLocalFile(tmp+'/dumpfile2')
            self.assertEqual(self.res.getValue(self.t3),9.)
            self.assertEqual(self.res.getValueType(),ValueType.Tensor)
            self.assertEqual(self.res.getTime(),9*mp.U.s)
            self.assertEqual(self.res.getPropertyID(),PropertyID.PID_ParticleSigma)
            self.assertEqual(self.res.getObjectID(),8)
            self.assertTrue(self.p3.getUnit().isCompatible(mp.U['kg/(m*s**2)']))
        
# python test_Property.py for stand-alone test being run
if __name__=='__main__': unittest.main()

        
        
    
        
