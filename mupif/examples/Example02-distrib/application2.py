import sys
import Pyro4
import logging
sys.path.extend(['..', '../../..'])
from mupif import *
import mupif.Physics.PhysicalQuantities as PQ

log = logging.getLogger()


@Pyro4.expose
class application2(Model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, metaData={}):
        super(application2, self).__init__(metaData=metaData)
        self.value = 0.0
        self.count = 0.0
        self.contrib = Property.ConstantProperty(
            (0.,), PropertyID.PID_Time, ValueType.Scalar, 's', PQ.PhysicalQuantity(0., 's'))

    def getProperty(self, propID, time, objectID=0):
        if propID == PropertyID.PID_Time:
            return Property.ConstantProperty(
                (self.value,), PropertyID.PID_Time, ValueType.Scalar, 's', time)
        else:
            raise APIError.APIError('Unknown property ID')

    def setProperty(self, property, objectID=0):
        if property.getPropertyID() == PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = property
        else:
            raise APIError.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value = self.value+self.contrib.inUnitsOf('s').getValue(tstep.getTime())[0]
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application2"
