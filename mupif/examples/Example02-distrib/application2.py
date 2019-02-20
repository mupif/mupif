import sys
sys.path.extend(['..','../../..'])

from mupif import *
import Pyro4
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

@Pyro4.expose
class application2(Model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self):
        super(application2, self).__init__()
        self.value = 0.0
        self.count = 0.0
        self.contrib = None
        self.setMetadata('Model.Model_description', 'Cummulate time')
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            log.debug('Getting property from this application2')
            return Property.ConstantProperty(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 'kg/m**3', time, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        log.debug("Solving step: %d %f%s %f%s" % (tstep.getNumber(), tstep.getTime().getValue(), tstep.getTime().getUnitName(), tstep.getTimeIncrement().getValue(), tstep.getTime().getUnitName() ) )
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib.inUnitsOf('kg/m**3').getValue(tstep.getTime())
        self.count = self.count+1
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')
    def getAssemblyTime(self,tstep):
        return tstep.getTime()
    def getApplicationSignature(self):
        return "Application2"
