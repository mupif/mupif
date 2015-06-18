from mupif import *

class PingServerApplication(Application.Application):
    """
    Simple application that computes an aritmetical average of a mapped property
    """
    def __init__(self, file, workdir):
        super(PingServerApplication, self).__init__(file, workdir)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Demo_Value):
            return Property.Property(self.count, PropertyID.PID_Demo_Value, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertID() == PropertyID.PID_Demo_Value):
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
