import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
from mupif import timestep
import mupif.physics.physicalquantities as PQ



class TimeStep_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_Init(self):

        time  = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        try:
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=time + dt,units=None, number=timestepnumber)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')


        time = PQ.makeQuantity(0.0,'s')
        try:
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=targetTime, units=None, number=timestepnumber)
        except TypeError:
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Exception not raised')

        dt = PQ.makeQuantity(0.5,'s')

        try:
            istep = timestep.TimeStep(time=time,dt=dt, targetTime=targetTime, units=None, number=timestepnumber)
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
        istep = timestep.TimeStep(time=time, dt=dt, targetTime=time + dt, unit=PQ.findUnit('m'), number=timestepnumber)



    def test_getTimeIncrement(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        istep = timestep.TimeStep(time=time, dt=dt, targetTime=time + dt, unit=PQ.findUnit('s'), number=timestepnumber)

        dT = istep.getTimeIncrement()
        self.assertTrue(dT.getValue() == dt)
        self.assertTrue(dT.getUnitName() == 's')


    def test_getTargetTime(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        istep = timestep.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=PQ.findUnit('s'), number=timestepnumber)

        tT = istep.getTargetTime()
        self.assertTrue(tT.getValue() == 2.0)
        self.assertTrue(tT.getUnitName() == 's')

    def test_getTimeStepNumber(self):
        time = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 1

        istep = timestep.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=PQ.findUnit('s'), number=timestepnumber)

        self.assertTrue(istep.getNumber() == 1)




if __name__ == '__main__': unittest.main()





