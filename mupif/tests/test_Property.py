import unittest,sys
sys.path.append('../..')

from mupif import *
from mupif.physics.physicalquantities import makeUnit as PU
from mupif.physics.physicalquantities import makeQuantity as PQ
import math
import mupif as mp
import numpy as np

class Property_TestCase(unittest.TestCase):
    def setUp(self):

        self.t1 = PQ(6,'s')
        self.t2 = PQ(15,'s')
        self.t3 = PQ(9,'s')

        
        self.p1=property.ConstantProperty(value=16.,propID=PropertyID.PID_Concentration,valueType=ValueType.Scalar,unit=mp.U['m'],time=self.t1,objectID=1)
        self.p2=property.ConstantProperty(value=7.,propID=PropertyID.PID_Velocity,valueType=ValueType.Vector,unit=mp.U['m/s'],time=self.t2,objectID=16)
        self.p3=property.ConstantProperty(value=9.,propID=PropertyID.PID_ParticleSigma,valueType=ValueType.Tensor,unit=mp.U['kg/m/s**2'],time=self.t3, objectID=8)

    def tearDown(self):
        
        self.p1=None
        self.p2=None
        self.p3=None

        self.t1 = None
        self.t2 = None
        self.t3 = None
        
# Testing getValue        
    def test_getValue(self):
        res=self.p1.getValue(PQ(6,'s'))
        self.assertEqual(res,16.,'error in getValue for p1')
        
        res=self.p2.getValue(self.t2)
        self.assertEqual(res,7.,'error in getValue for p2')  
        
        res=self.p3.getValue(self.t3)
        self.assertEqual(res,9.,'error in getValue for p3')
        
# Testing getValueType        
    def test_getValueType(self):
        self.assertEqual(self.p1.getValueType(),ValueType.Scalar,'wrong ValueType for p1')
        
        self.assertEqual(self.p2.getValueType(),ValueType.Vector,'wrong ValueType for p2')
        
        self.assertEqual(self.p3.getValueType(),ValueType.Tensor,'wrong ValueType for p3')
        
# Testing getTime
    def test_getTime(self):
        self.assertEqual(self.p1.getTime().inUnitsOf('s').getValue(),6,'wrong getTime for p1')
   
        self.assertEqual(self.p2.getTime().inUnitsOf('s').getValue(),15,'wrong getTime for p2')        
    
        self.assertEqual(self.p3.getTime().inUnitsOf('s').getValue(),9,'wrong getTime for p3')  
        
# Testing getPropertyID
    def test_getPropertyID(self):
        self.assertEqual(self.p1.getPropertyID(),PropertyID.PID_Concentration,'wrong getPropertyID for p1')
        
        self.assertEqual(self.p2.getPropertyID(),PropertyID.PID_Velocity,'wrong getPropertyID for p2')
        
        self.assertEqual(self.p3.getPropertyID(),PropertyID.PID_ParticleSigma,'wrong getPropertyID for p3')
        
    def test_getObjectID(self):
        self.assertEqual(self.p1.getObjectID(),1)
        self.assertEqual(self.p2.getObjectID(),16)
        self.assertEqual(self.p3.getObjectID(),8)
        
    def test_getUnits(self):
        self.assertTrue(self.p1.getUnits().isCompatible(mp.U['m']))
        self.assertTrue(self.p2.getUnits().isCompatible(mp.U['m/s']))
        self.assertTrue(self.p3.getUnits().isCompatible(mp.U['kg/m/s**2']))
        
    def test_dumpToLocalFile(self):
        self.res=None
        self.p1.dumpToLocalFile('dumpfile')
        self.res=property.ConstantProperty.loadFromLocalFile('dumpfile')
        self.assertEqual(self.res.getValue(self.t1),16.)
        self.assertEqual(self.res.getValueType(),ValueType.Scalar,)
        self.assertEqual(self.res.getTime(),PQ(6,'s'))
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_Concentration)
        self.assertEqual(self.res.getObjectID(),1)
        self.assertTrue(self.res.getUnits().isCompatible(mp.U['m']))
        
        self.res=None
        self.p3.dumpToLocalFile('dumpfile2')
        self.res=property.ConstantProperty.loadFromLocalFile('dumpfile2')
        self.assertEqual(self.res.getValue(self.t3),9.)
        self.assertEqual(self.res.getValueType(),ValueType.Tensor,'wrong dumpToLocal File_ValueType for p3')
        self.assertEqual(self.res.getTime(),PQ(9,'s'),'wrong dumpToLocal File_getTime for p3')
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_ParticleSigma,'wrong dumpToLocal File_getPropertyID for p3')
        self.assertEqual(self.res.getObjectID(),8,'wrong dumpToLocal File_getObjectID for p3')
        self.assertTrue(self.p3.getUnits().isCompatible(mp.U['kg/m/s**2']))
        
# python test_Property.py for stand-alone test being run
if __name__=='__main__': unittest.main()

        
        
    
        
