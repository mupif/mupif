import sys
sys.path.append('../../..')
from mupif import *
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

class application1(Model.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self):
        #calls constructor from Application module
        super(application1, self).__init__()
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.ConstantProperty(self.value, PropertyID.PID_Concentration, ValueType.Scalar, 'kg/m**3', time)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = self.getAssemblyTime(tstep).inUnitsOf('s').getValue()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')
    def getAssemblyTime (self, tstep):
        return tstep.getTime()


class application2(Model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self):
        super(application2, self).__init__()
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return Property.ConstantProperty(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 'kg/m**3', time)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib.inUnitsOf('kg/m**3').getValue(self.getAssemblyTime(tstep))
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')
    def getAssemblyTime (self, tstep):
        return tstep.getTime()

time  = 0
timestepnumber=0
targetTime = 1.0

app1 = application1()
app2 = application2()

app1Metadata = {'Model.Model_ID' : 'Model ID-1234',
                'Model.Model_name' : 'Simple application cummulating calling time',
                'Model.Model_description' : 'Cummulates calling time',
                'Model.Model_time_lapse' : '0.01 s',
                'Model.Inputs_and_relation_to_Data' : [{'Input_name':'Time', 'Input_description':'Time of the task', 'Input_type': 'PhysicalQuantity', 'Input_object_type':'mupif.PQ.PhysicalQuantity', 'Input_object_id': None, 'Input_optional':True,'Input_units':'s'}],
                'Model.Outputs_and_relation_to_Data' : [{'Output_name':'Concentration', 'Output_description':'Concentration', 'Output_type': 'ConstantProperty', 'Output_object_type':'mupif.PropertyID.PID_Concentration', 'Output_object_id': None, 'Output_optional':True,'Output_units':'kg/m**3'}]
               }

app1.initialize(metaData=app1Metadata)
app1.printMetadata()

app1.toJSONFile('aa.json')
aa = MupifObject.MupifObject('aa.json')
aa.printMetadata()

#TODO - update app2
app2.initialize(metaData=app1Metadata)
app2.printMetadata()




while (abs(time -targetTime) > 1.e-6):

    #determine critical time step
    dt = min(app1.getCriticalTimeStep().inUnitsOf('s').getValue(),
             app2.getCriticalTimeStep().inUnitsOf('s').getValue())
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    # create a time step
    istep = TimeStep.TimeStep(time, dt, targetTime, 's', timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.getProperty(PropertyID.PID_Concentration, app2.getAssemblyTime(istep))
        app2.setProperty (c)
        # solve second sub-problem 
        app2.solveStep(istep)
        # get the averaged concentration
        prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, app2.getAssemblyTime(istep))
        #print (istep.getTime(), c, prop)
        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f concentration %5.2f, running average %5.2f" % (atime.getValue(), c.getValue(atime), prop.getValue(atime)))
        
        
    except APIError.APIError as e:
        log.error("mupif.APIError occurred:",e)
        log.error("Test FAILED")
        raise

if (abs(prop.getValue(istep.getTime())-0.55) <= 1.e-4):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate();
app2.terminate();
