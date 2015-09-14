from __future__ import print_function, division
import unittest
from mupif import *

class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        #calls constructor from Application module
        super(application1, self).__init__(file)
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.Property(self.value, PropertyID.PID_Concentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1


class application2(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        super(application2, self).__init__(file)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return Property.Property(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property.getValue()
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1.0


class TestEx01(unittest.TestCase):
    def setUp(self):
        self.app1,self.app2=application1(None),application2(None)
    def testEverything(self):
        app1,app2=self.app1,self.app2
        time  = 0
        timestepnumber=0
        targetTime = 1.0
        while (abs(time -targetTime) > 1.e-6):
            #determine critical time step
            dt = min(app1.getCriticalTimeStep(), app2.getCriticalTimeStep())
            #update time
            time = time+dt
            if (time > targetTime):
                #make sure we reach targetTime at the end
                time = targetTime
            timestepnumber = timestepnumber+1
            # create a time step
            istep = TimeStep.TimeStep(time, dt, timestepnumber)

            # solve problem 1
            app1.solveStep(istep)
            #request Concentration property from app1
            c = app1.getProperty(PropertyID.PID_Concentration, istep)
            # register Concentration property in app2
            app2.setProperty (c)
            # solve second sub-problem 
            app2.solveStep(istep)
            # get the averaged concentration
            prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep)
            print ("Time: %5.2f concentraion %5.2f, running average %5.2f" % (istep.getTime(), c.getValue(), prop.getValue()))
        self.assertAlmostEqual(prop.getValue(),0.55)
    def tearDown(self):
        # terminate
        self.app1.terminate();
        self.app2.terminate();

# python test_ex01.py for stand-alone test being run
if __name__=='__main__': unittest.main()

