import unittest
import mupif as mp
import numpy as np

mp.MultiPiecewiseLinFunction2 = mp.multipiecewiselinfunction.MultiPiecewiseLinFunction2


def assertAlmostEqual_Quantity(self, a1, a2):
    self.assertEqual(a1.unit, a2.unit)
    np.testing.assert_array_almost_equal(a1.value, a2.value)


unittest.TestCase.assertAlmostEqual_Quantity = assertAlmostEqual_Quantity


class Test_MultiPiecewiseLinFunction(unittest.TestCase):
    def setUp(self):
        self.mplf = mp.MultiPiecewiseLinFunction()
        self.mplf.setXData([0., 1., 2., 3.], mp.U.m)
        self.mplf.addYData([(5.,), (6.,), (7.,), (8.,)], mp.U.s, mp.DataID.PID_Time, mp.ValueType.Scalar)
        self.mplf.addYData([(15.,), (16.,), (17.,), (18.,)], mp.U.m, mp.DataID.PID_Length, mp.ValueType.Scalar)

    def testEvaluate(self):
        # produces property with value (6.5,) s
        self.assertAlmostEqual_Quantity(self.mplf.evaluate(1.5*mp.U.m, mp.DataID.PID_Time), 6.5*mp.U.s)
        # produces property with value (16.5,) m
        self.assertAlmostEqual_Quantity(self.mplf.evaluate(1.5*mp.U.m, mp.DataID.PID_Length), 16.5*mp.U.m)
        self.assertAlmostEqual_Quantity(self.mplf.evaluate(1000*mp.U.mm, mp.DataID.PID_Time), 6.*mp.U.s)


# class Test_MultiPiecewiseLinFunction2(unittest.TestCase):
#     def setUp(self):
#         self.m2 = mp.MultiPiecewiseLinFunction(x=mp.Quantity(value=[0., 1., 2., 3.], unit=mp.U.m))
#         self.m2.addY(mp.Property(value=[5., 6., 7., 8.], unit=mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar))
#         self.m2.addY(mp.Property(value=[15., 16., 17., 18.], unit=mp.U.m, propID=mp.DataID.PID_Length, valueType=mp.ValueType.Scalar))
#
#     def testEvaluate(self):
#         self.assertRaises(ValueError, lambda: self.m2.evaluate(-1*mp.U.m, mp.DataID.PID_Time))
#         self.assertAlmostEqual_Quantity(self.m2.evaluate(1.5*mp.U.m, mp.DataID.PID_Time), 6.5*mp.U.s)
#         self.assertAlmostEqual_Quantity(self.m2.evaluate(1.5*mp.U.m, mp.DataID.PID_Length), 16.5*mp.U.m)
#         self.assertAlmostEqual_Quantity(self.m2.evaluate(1500*mp.U.mm, mp.DataID.PID_Length), 16.5*mp.U.m)
