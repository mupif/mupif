import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
from mupif import TimeStep
import mupif.Physics.PhysicalQuantities as PQ



class TimeStep_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_Init(self):

        time  = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        try:
            istep = TimeStep.TimeStep(time, dt, time + dt, None, timestepnumber)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')


        time = PQ.PhysicalQuantity('0.0 s')
        try:
            istep = TimeStep.TimeStep(time, dt, targetTime, None, timestepnumber)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        dt = PQ.PhysicalQuantity('0.5 s')

        try:
            istep = TimeStep.TimeStep(time, dt, targetTime, None, timestepnumber)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')


        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        # @todo what sould this do?
        istep = TimeStep.TimeStep(time, dt, time + dt, 'm', timestepnumber)



    def test_getTimeIncrement(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        istep = TimeStep.TimeStep(time, dt, time + dt, 's', timestepnumber)

        dT = istep.getTimeIncrement()
        self.assertTrue(dT.getValue() == dt)
        self.assertTrue(dT.getUnitName() == 's')


    def test_getTargetTime(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        istep = TimeStep.TimeStep(time, dt, targetTime, 's', timestepnumber)

        tT = istep.getTargetTime()
        self.assertTrue(tT.getValue() == 2.0)
        self.assertTrue(tT.getUnitName() == 's')

    def test_getTimeStepNumber(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 1

        istep = TimeStep.TimeStep(time, dt, targetTime, 's', timestepnumber)

        self.assertTrue(istep.getNumber() == 1)




if __name__ == '__main__': unittest.main()





