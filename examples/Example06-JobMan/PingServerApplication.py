import sys
sys.path.append('../..')
#from mupif import *
from mupif import Application
from mupif import PropertyID
from mupif import FieldID
from mupif import Mesh
from mupif import Field
from mupif import ValueType
from mupif import Vertex
from mupif import Cell
from mupif import PyroUtil
from mupif import Property
from mupif import IntegrationRule

class PingServerApplication(Application.Application):
    """
    Simple application that computes an aritmetical average of a mapped property
    """
    def __init__(self):
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return Property.Property(float(self.value)/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, None, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertID() == PropertyID.PID_Concentration):
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

    def getApplicationSignature(self):
        return "PingServerApplication"
