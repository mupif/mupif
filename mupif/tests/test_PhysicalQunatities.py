import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
import mupif.Physics.PhysicalQuantities as PQ


class PhysicalQuantity_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_Init(self):

        V = PQ.PhysicalQuantity('3.6 km/h')
        velocity = V.inBaseUnits()
        self.assertTrue(velocity.value == 1.0)
        self.assertEqual(velocity.getUnitName(), 'm/s')

        try:
            V = PQ.PhysicalQuantity('s m s')
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')


        try:
            V = PQ.PhysicalQuantity('2 m s')
        except SyntaxError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')


    def test_SumFail(self):
        V = PQ.PhysicalQuantity('3.6 km/h')
        F = PQ.PhysicalQuantity('20 N')
        try:
            V._sum(F, 1, 1)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:',e)
        else:
            self.fail('Exception not raised')

        try:
            V._sum(10, 1, 1)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')




    def test_Add(self):
        V1 = PQ.PhysicalQuantity('1 km/h')
        V2 = PQ.PhysicalQuantity('2 km/h')
        V3 = V2+V1
        self.assertEqual(V3.getValue(),3)
    def test_Sub(self):
        V1 = PQ.PhysicalQuantity('1 km/h')
        V2 = PQ.PhysicalQuantity('2 km/h')
        V3 = V2-V1
        self.assertEqual(V3.getValue(), 1)
    def test_Rsub(self):
        V1 = PQ.PhysicalQuantity('1 km/h')
        V2 = PQ.PhysicalQuantity('2 km/h')
        V3 = V2.__rsub__(V1)
        self.assertEqual(V3.getValue(), -1)

    def test_Rsub(self):
        V1 = PQ.PhysicalQuantity('1 km/h')
        V2 = PQ.PhysicalQuantity('2 km/h')
        V3 = V2.__rsub__(V1)
        self.assertEqual(V3.getValue(), -1)

    def test_Lower(self):
        V1 = PQ.PhysicalQuantity('1 m/s')
        V2 = PQ.PhysicalQuantity('2 m/s')
        V3 = PQ.PhysicalQuantity('3.6 km/h')
        self.assertTrue(V1 < V2)
        self.assertFalse(V1 > V2)
        self.assertFalse(V1 == V2)
        self.assertTrue(V3 < V2)
        self.assertFalse(V3 > V2)
        self.assertTrue(V1 == V3)

    def test_Mul(self):
        # multiplication with a number
        len = PQ.PhysicalQuantity('1 m')
        len2 = 2*len
        lenTest = PQ.PhysicalQuantity('2 m')
        self.assertEqual(len2, lenTest)
        # multiplication with a physical quantity without units
        len = PQ.PhysicalQuantity('1 m')
        len2 = PQ.PhysicalQuantity('2 none')
        lenTest1 = len*len2
        lenTest2 = PQ.PhysicalQuantity('2 m')
        self.assertEqual(lenTest1, lenTest2)
        # multiplication with a physical quantity with units
        len = PQ.PhysicalQuantity('1 m')
        time = PQ.PhysicalQuantity('2 s')
        w = len*time
        ms = PQ.PhysicalQuantity('2 m*s')
        self.assertEqual(w,ms)

        w = len * 5
        len5 = PQ.PhysicalQuantity('5 m')
        self.assertEqual(w, len5)





    def test_TrueDiv(self):
        # division with a number
        len = PQ.PhysicalQuantity('1 m')
        len2 = len / 2
        lenTest = PQ.PhysicalQuantity('0.5 m')
        self.assertEqual(len2, lenTest)
        # division with a physical quantity without units
        len = PQ.PhysicalQuantity('1 m')
        len2 = PQ.PhysicalQuantity('2 none')
        lenTest1 = len / len2
        lenTest2 = PQ.PhysicalQuantity('0.5 m')
        self.assertEqual(lenTest1, lenTest2)
        # division with a physical quantity with units
        len = PQ.PhysicalQuantity('1 m')
        time = PQ.PhysicalQuantity('2 s')
        w = len / time
        ms = PQ.PhysicalQuantity('0.5 m/s')
        self.assertEqual(w, ms)


    def test_RTrueDiv(self):
        # division with a number
        len = PQ.PhysicalQuantity('1 m/s')
        len2 = 2/len
        lenTest = PQ.PhysicalQuantity('2.0 s/m')
        self.assertEqual(len2, lenTest)



    def test_Pow(self):
        V = PQ.PhysicalQuantity('1 km/h')
        F = PQ.PhysicalQuantity('20 m')
        try:
            A = V**F
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        r = PQ.PhysicalQuantity('400 m*m')
        t = F**2
        self.assertEqual(r, r)

    def test_Rpow(self):
        F = PQ.PhysicalQuantity('2 m')
        try:
            A = 2**F
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

    def test_Abs(self):
        F = PQ.PhysicalQuantity('2 m')
        mF = PQ.PhysicalQuantity('-2 m')

        amF = mF.__abs__()
        self.assertEqual(F, amF)



    def test_Neg(self):
        F = PQ.PhysicalQuantity('2 m')
        mF = PQ.PhysicalQuantity('-2 m')

        nF = F.__neg__()
        nmF = mF.__neg__()

        self.assertEqual(F, nmF)
        self.assertEqual(mF, nF)

    def test_Bool(self):
        A = PQ.PhysicalQuantity('0 m')
        B = PQ.PhysicalQuantity('1 m')
        self.assertFalse(A.__bool__())
        self.assertTrue(B.__bool__())

    def test_inUnitsOf(self):
        A = PQ.PhysicalQuantity('2 m')
        ## @todo this is not working
        #units = [[] for i in range(2)]
        #units[0].append('km')
        #units[1].append('mm')
        #B = A.inUnitsOf(units)



    def test_inBaseUnits(self):
        A = PQ.PhysicalQuantity('12.96 km*km/h/h')
        B = A.inBaseUnits()
        C = PQ.PhysicalQuantity('1 m*m/s/s')
        self.assertEqual(C, A)
        #@todo missing test of len(num) == 0


    def test_getUnitName(self):
        A = PQ.PhysicalQuantity('152 m*km/N/W')
        s = A.getUnitName()
        #self.assertEqual(s,'m*km/W/N')
        self.assertEqual(s, 'm*km/N/W')

    def test_Sqrt(self):
        A = PQ.PhysicalQuantity('4 m*m')
        B = A.sqrt()
        C = PQ.PhysicalQuantity('2 m')
        self.assertEqual(B, C)
    def test_sin(self):
        A = PQ.PhysicalQuantity('4 m')
        try:
            B = A.sin()
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        A = PQ.PhysicalQuantity('3.14159265358979323846264 rad')
        B = A.sin()
        self.assertAlmostEqual(B, 0)

    def test_cos(self):
        A = PQ.PhysicalQuantity('4 s')
        try:
            B = A.cos()
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        A = PQ.PhysicalQuantity('3.14159265358979323846264 rad')
        B = A.sin()
        self.assertAlmostEqual(B, 0)

    def test_tan(self):
        A = PQ.PhysicalQuantity('4 N')
        try:
            B = A.tan()
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        A = PQ.PhysicalQuantity('3.14159265358979323846264 rad')
        B = A.tan()
        self.assertAlmostEqual(B, 0)


    def test_cmp(self):
        timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])
        timeUnits2 = PQ.PhysicalUnit('s', 2., [0, 0, 1, 0, 0, 0, 0, 0, 0])
        timeUnits3 = PQ.PhysicalUnit('s', -1., [0, 0, 1, 0, 0, 0, 0, 0, 0])
        timeUnits4 = PQ.PhysicalUnit('s', 1., [0, 0, 1, 0, 0, 0, 0, 0, 0])
        temperatureUnits = PQ.PhysicalUnit('K',   1.,    [0,0,0,0,1,0,0,0,0])


        try:
            a = timeUnits.__cmp__(temperatureUnits)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        self.assertTrue(timeUnits.__cmp__(timeUnits2) < 0)
        self.assertTrue(timeUnits.__cmp__(timeUnits3) > 0)
        self.assertTrue(timeUnits.__cmp__(timeUnits4) == 0)
        self.assertTrue(timeUnits.__cmp__(5) == -1)

    # python test_Cell.py for stand-alone test being run
if __name__ == '__main__': unittest.main()


