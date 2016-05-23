import unittest
from mupif import *
from mupif.Physics.PhysicalQuantities import PhysicalUnit as PQ 
import math
import numpy as np

class Property_TestCase(unittest.TestCase):
    def setUp(self):
        
        self.p1=Property.Property(16.,PropertyID.PID_Concentration,ValueType.Scalar,6,PQ({'m': 1}, 1,(1,0,0,0,0,0,0)),1)
        self.p2=Property.Property(7.,PropertyID.PID_Velocity,ValueType.Vector,15,PQ({'m': 1, 's': -1}, 1,(1,0,1,0,0,0,0)),16)
        self.p3=Property.Property(16.,PropertyID.PID_ParticleSigma,ValueType.Tensor,9,PQ({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0)),8)

    def tearDown(self):
        
        self.p1=None
        self.p2=None
        self.p3=None
             
# Testing getValue        
    def test_getValue(self):
        res=self.p1.getValue()
        self.assertEqual(res,16.,'error in getValue for p1')
        
        res=self.p2.getValue()
        self.assertEqual(res,7.,'error in getValue for p2')  
        
        res=self.p3.getValue()
        self.assertEqual(res,16.,'error in getValue for p3')
# Testing getValueType        
    def test_getValueType(self):
        self.assertEqual(self.p1.getValueType(),ValueType.Scalar,'wrong ValueType for p1')
        
        self.assertEqual(self.p2.getValueType(),ValueType.Vector,'wrong ValueType for p2')
        
        self.assertEqual(self.p3.getValueType(),ValueType.Tensor,'wrong ValueType for p3')
        
# Testing getTime
    def test_getTime(self):
        self.assertEqual(self.p1.getTime(),6,'wrong getTime for p1')
   
        self.assertEqual(self.p2.getTime(),15,'wrong getTime for p2')        
    
        self.assertEqual(self.p3.getTime(),9,'wrong getTime for p3')  
        
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
        self.assertEqual(self.p1.getUnits().isCompatible(PQ({'m':1}, 1,(1,0,0,0,0,0,0))), True, 'wrong getUnits for p1')
        
        self.assertEqual(self.p2.getUnits().isCompatible(PQ({'m': 1, 's': -1}, 1,(1,0,1,0,0,0,0))),True,'wrong getUnits for p2')
        
        self.assertEqual(self.p3.getUnits().isCompatible(PQ({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0))),True,'wrong getUnits for p3')
        
#Testing dumpToLocalFile and loadFromLocalFile     
    def test_dumpToLocalFile(self):
        self.res=Property.Property(0.,0,0,0,0)
        self.p1.dumpToLocalFile('dumpfile')
        self.res=self.p1.loadFromLocalFile('dumpfile')
        self.assertEqual(self.res.getValue(),16.,'error in dumpToLocal File_getValue for p1')
        self.assertEqual(self.res.getValueType(),ValueType.Scalar,'wrong in dumpToLocal File_ValueType for p1')
        self.assertEqual(self.res.getTime(),6,'wrong dumpToLocal File_getTime for p1')
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_Concentration,'wrong dumpToLocal File_getPropertyID for p1')
        self.assertEqual(self.res.getObjectID(),1,'wrong dumpToLocal File_getObjectID for p1')
        self.assertEqual(self.res.getUnits().isCompatible(PQ({'m':1}, 1,(1,0,0,0,0,0,0))), True, 'wrong getUnits for p1')
        
        self.res=Property.Property(0.,0,0,0,0)
        self.p3.dumpToLocalFile('dumpfile')
        self.res=self.p3.loadFromLocalFile('dumpfile')
        self.assertEqual(self.res.getValue(),16.,'error in dumpToLocal File_getValue for p3')
        self.assertEqual(self.res.getValueType(),ValueType.Tensor,'wrong dumpToLocal File_ValueType for p3')
        self.assertEqual(self.res.getTime(),9,'wrong dumpToLocal File_getTime for p3')
        self.assertEqual(self.res.getPropertyID(),PropertyID.PID_ParticleSigma,'wrong dumpToLocal File_getPropertyID for p3')
        self.assertEqual(self.res.getObjectID(),8,'wrong dumpToLocal File_getObjectID for p3')
        self.assertEqual(self.p3.getUnits().isCompatible(PQ({'kg': 1, 's': -2, 'm': -1}, 1,(1,1,1,0,0,0,0))),True,'wrong dumpToLocal File_getUnits for p3')
        
# python test_Property.py for stand-alone test being run
if __name__=='__main__': unittest.main()

        
        
    
        
