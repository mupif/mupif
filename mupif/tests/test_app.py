import sys
sys.path.append('../..')

import unittest
import mupif
from mupif import *
from mupif.tests import demo

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app1,self.app2=demo.AppCurrTime(file=None),demo.AppPropAvg(file=None)
    def test_app(self):
        app1,app2=self.app1,self.app2
        time  = 0
        timestepnumber=0
        targetTime = 1.0
        while (abs(time -targetTime) > 1.e-6):
            #determine critical time step
            dt = min(app1.getCriticalTimeStep().inUnitsOf(mupif.U.s).getValue(),
                     app2.getCriticalTimeStep().inUnitsOf(mupif.U.s).getValue())
            #update time
            time = time+dt
            if (time > targetTime):
                #make sure we reach targetTime at the end
                time = targetTime
            timestepnumber = timestepnumber+1
            # create a time step
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mupif.U.s, number=timestepnumber)

            # solve problem 1
            app1.solveStep(istep)
            #request Concentration property from app1
            c = app1.getProperty(PropertyID.PID_Concentration, app2.getAssemblyTime(istep))
            # register Concentration property in app2
            app2.setProperty (c)
            # solve second sub-problem 
            app2.solveStep(istep)
            # get the averaged concentration
            prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, time*mupif.Q.s)
            print (f"Time: {istep.getTime().getValue()} concentraion {c.getValue(istep.getTime())}, running average {prop.getValue(istep.getTime())}")
        self.assertAlmostEqual(prop.getValue(istep.getTime()),0.55)
    def tearDown(self):
        # terminate
        self.app1.terminate();
        self.app2.terminate();

# python test_ex01.py for stand-alone test being run
if __name__=='__main__': unittest.main()

