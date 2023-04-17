import unittest
import sys
sys.path.append('../..')

from mupif import *
import tempfile
import mupif as mp
import numpy as np


class Property_TestCase(unittest.TestCase):
    def setUp(self):

        self.t1 = 6*mp.U.s
        self.t2 = 15*mp.U.s
        self.t3 = 9*mp.U.s

        self.p1 = property.ConstantProperty(value=16., propID=DataID.PID_Concentration, valueType=ValueType.Scalar, unit=mp.U['m'], time=self.t1)
        self.p2 = property.ConstantProperty(value=7., propID=DataID.PID_Velocity, valueType=ValueType.Vector, unit=mp.U['m/s'], time=self.t2)
        self.p3 = property.ConstantProperty(value=9., propID=DataID.PID_ParticleSigma, valueType=ValueType.Tensor, unit=mp.U['kg/(m*s**2)'], time=self.t3)

    def test_getValue(self):
        res = self.p1.getValue(6*mp.U.s)
        self.assertEqual(res, 16.)
        self.assertEqual(self.p1.getQuantity(6*mp.U.s), 16.*mp.U.m)

        res = self.p2.getValue(self.t2)
        self.assertEqual(res, 7.)

        res = self.p3.getValue(self.t3)
        self.assertEqual(res, 9.)

    def test_getValueType(self):
        self.assertEqual(self.p1.getValueType(), ValueType.Scalar)
        self.assertEqual(self.p2.getValueType(), ValueType.Vector)
        self.assertEqual(self.p3.getValueType(), ValueType.Tensor)

    def test_getTime(self):
        self.assertEqual(self.p1.getTime().inUnitsOf('s').getValue(), 6)
        self.assertEqual(self.p2.getTime().inUnitsOf('s').getValue(), 15)
        self.assertEqual(self.p3.getTime().inUnitsOf('s').getValue(), 9)

    def test_getPropertyID(self):
        self.assertEqual(self.p1.getPropertyID(), DataID.PID_Concentration)
        self.assertEqual(self.p2.getPropertyID(), DataID.PID_Velocity)
        self.assertEqual(self.p3.getPropertyID(), DataID.PID_ParticleSigma)

    def test_getUnit(self):
        self.assertTrue(self.p1.getUnit().isCompatible(mp.U['m']))
        self.assertTrue(self.p2.getUnit().isCompatible(mp.U['m/s']))
        self.assertTrue(self.p3.getUnit().isCompatible(mp.U['kg/(m*s**2)']))

    def test_saveLoadHdf5(self):
        with tempfile.TemporaryDirectory() as tmp:
            for p in self.p1,self.p2,self.p3:
                p.saveHdf5(tmp+'/prop.h5')
                res=property.ConstantProperty.loadHdf5(tmp+'/prop.h5')
                self.assertEqual(p.getValue(p.getTime()),res.getValue(res.getTime()))
                self.assertEqual(p.getValueType(),       res.getValueType())
                self.assertEqual(p.getTime(),            res.getTime())
                self.assertEqual(p.getPropertyID(),      res.getPropertyID())
                self.assertEqual(p.getQuantity(),        res.getQuantity())
                #import shutil
                #shutil.copy(tmp+'/prop.h5',f'/tmp/mupif_prop_t_{p.getTime().value}.hdf5')


class TemporalProperty_TestCase(unittest.TestCase):
    def setUp(self):
        self.tp=mp.TemporalProperty(times=[1,2,3,4,5]*mp.U.s,quantity=[10,20,30,40,50]*mp.U['m/s'],valueType=ValueType.Scalar,propID=DataID.PID_Concentration)
        self.tpVec=mp.TemporalProperty(times=[1,2,3,4,5]*mp.U.s,quantity=[[10,1,.1],[20,2,.2],[30,3,.3],[40,4,.4],[50,5,.5]]*mp.U['m/s'],valueType=ValueType.Scalar,propID=DataID.PID_Concentration)
    def test_create(self):
        kw=dict(propID=DataID.PID_Concentration,valueType=ValueType.Scalar)
        self.assertRaises(ValueError,lambda: TemporalProperty(times=[]*mp.U.s,quantity=[1,2,3]*mp.U.s,**kw))
        # dimensionmismatch
        self.assertRaises(ValueError,lambda: TemporalProperty(times=[1,2,3]*mp.U.s,quantity=[1,2]*mp.U.s,**kw))
        # times not in time units
        self.assertRaises(ValueError,lambda: TemporalProperty(times=[1,2,3]*mp.U.km,quantity=[1,2]*mp.U.s,**kw))
        # time not a 1D array
        self.assertRaises(ValueError,lambda: TemporalProperty(times=[[1,1],[2,2]]*mp.U.km,quantity=[1,2]*mp.U.s,**kw))
    def test_evaluate(self):
        self.assertEqual(self.tp.evaluate(time=1*mp.U.s).quantity,10*mp.U['m/s'])
        self.assertEqual(self.tp.evaluate(time=3500*mp.U.ms).quantity,35*mp.U['m/s'])
        self.assertTrue(np.all(self.tpVec.evaluate(time=1*mp.U.s).quantity==[10,1,.1]*mp.U['m/s']))
        self.assertRaises(ValueError,lambda: self.tp.evaluate(time=0*mp.U.s)) # out of range
        pass



# python test_Property.py for stand-alone test being run
if __name__ == '__main__':
    unittest.main()
