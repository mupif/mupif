from mupif import *
import Pyro4
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

@Pyro4.expose
class application2(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file=None, workdir=None):
        super(application2, self).__init__(file, workdir)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            log.debug('Getting property from this application2')
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
        log.debug("Solving step: %d %f %f" % (tstep.number, tstep.time, tstep.dt) )
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib
        self.count = self.count+1
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')
    def getApplicationSignature(self):
        return "Application2"
