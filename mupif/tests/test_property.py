import unittest
import sys
sys.path.append('../..')

from mupif import *
import tempfile
import mupif as mp


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

# python test_Property.py for stand-alone test being run
if __name__ == '__main__':
    unittest.main()
