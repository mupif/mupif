import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
from mupif import timestep
import mupif.physics.physicalquantities as PQ
import pydantic


class TimeStep_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_Init(self):

        time  = 0.0
        dt = 0.5
        targetTime = 2.0
        timestepnumber = 0

        with self.assertRaises(pydantic.ValidationError): 
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=time + dt,unit=None, number=timestepnumber)

        time = PQ.makeQuantity(0.0,'s')
        with self.assertRaises(pydantic.ValidationError):
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=None, number=timestepnumber)

        dt = PQ.makeQuantity(0.5,'s')

        with self.assertRaises(pydantic.ValidationError):
            istep = timestep.TimeStep(time=time,dt=dt, targetTime=targetTime, unit=None, number=timestepnumber)


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





