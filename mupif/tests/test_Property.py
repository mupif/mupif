import unittest,sys
sys.path.append('../..')

from mupif import *
from mupif.physics.physicalquantities import makeUnit as PU
from mupif.physics.physicalquantities import makeQuantity as PQ
import math
import numpy as np

class Property_TestCase(unittest.TestCase):
    def setUp(self):

        self.t1 = PQ(6,'s')
        self.t2 = PQ(15,'s')
        self.t3 = PQ(9,'s')

        
        self.p1=property.ConstantProperty(value=16.,propID=PropertyID.PID_Concentration,valueType=ValueType.Scalar,unit=PU({'m': 1}, 1,(1,0,0,0,0,0,0)),time=self.t1,objectID=1)
        self.p2=property.ConstantProperty(value=7.,propID=PropertyID.PID_Velocity,valueType=ValueType.Vector,unit=PU({'m': 1, 's': -1}, 1,(1,0,1,0,0,0,0)),time=self.t2,objectID=16)
        self.p3=property.ConstantProperty(value=9.,propID=PropertyID.PID_ParticleSigma,valueType=ValueType.Tensor,unit=PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),time=self.t3, objectID=8)

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
        
#Testing getObjectID        
    def test_getObjectID(self):
        self.assertEqual(self.p1.getObjectID(),1,'wrong getObjectID for p1')
        
        self.assertEqual(self.p2.getObjectID(),16,'wrong getObjectID for p2')
        
        self.assertEqual(self.p3.getObjectID(),8,'wrong getObjectID for p3')
        
#Testing getUnits
    def test_getUnits(self):
        self.assertEqual(self.p1.getUnits().isCompatible(PU({'m':1}, 1,(1,0,0,0,0,0,0))), True, 'wrong getUnits for p1')
        
        self.assertEqual(self.p2.getUnits().isCompatible(PU({'m': 1, 's': -1}, 1,(1,0,1,0,0,0,0))),True,'wrong getUnits for p2')
        
        self.assertEqual(self.p3.getUnits().isCompatible(PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0))),True,'wrong getUnits for p3')
        
#Testing dumpToLocalFile and loadFromLocalFile     
    def test_dumpToLocalFile(self):
        self.res=None
        self.p1.dumpToLocalFile('dumpfile')
        self.res=property.ConstantProperty.loadFromLocalFile('dumpfile')
        self.assertEqual(self.res.getValue(self.t1),16.,'error in dumpToLocal File_getValue for p1')
        self.assertEqual(self.res.getValueType(),ValueType.Scalar,'wrong in dumpToLocal File_ValueType for p1')
        self.assertEqual(self.res.getTime(),PQ(6,'s'),'wrong dumpToLocal File_getTime for p1')
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_Concentration,'wrong dumpToLocal File_getPropertyID for p1')
        self.assertEqual(self.res.getObjectID(),1,'wrong dumpToLocal File_getObjectID for p1')
        self.assertEqual(self.res.getUnits().isCompatible(PU({'m':1}, 1,(1,0,0,0,0,0,0))), True, 'wrong getUnits for p1')
        
        self.res=None
        self.p3.dumpToLocalFile('dumpfile2')
        self.res=property.ConstantProperty.loadFromLocalFile('dumpfile2')
        self.assertEqual(self.res.getValue(self.t3),9.,'error in dumpToLocal File_getValue for p3')
        self.assertEqual(self.res.getValueType(),ValueType.Tensor,'wrong dumpToLocal File_ValueType for p3')
        self.assertEqual(self.res.getTime(),PQ(9,'s'),'wrong dumpToLocal File_getTime for p3')
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_ParticleSigma,'wrong dumpToLocal File_getPropertyID for p3')
        self.assertEqual(self.res.getObjectID(),8,'wrong dumpToLocal File_getObjectID for p3')
        self.assertEqual(self.p3.getUnits().isCompatible(PU({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0))),True,'wrong dumpToLocal File_getUnits for p3')
        
# python test_Property.py for stand-alone test being run
if __name__=='__main__': unittest.main()

        
        
    
        
