import sys
sys.path.append('../..')

from mupif import Application
from mupif import EnsightReader
from mupif import FieldID


class Celsian(Application.Application):
    """
    An abstract class representing an application and its interface (API).

    The purpose of this class is to define abstract services for data exchange and steering.
    This interface has to be implemented/provided by any application.
    The data exchange is performed by the means of new data types introduced in the framework,
    namely properties and fields. 
    New abstract data types (properties, fields) allow to hide all implementation details 
    related to discretization and data storage.
    """
    def __init__ (self, file):
        self.reader = EnsightReader.EnsightReader() 
        self.mesh = None

    def getField(self, fieldID, time):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        ARGS:
            fieldID (FieldID):  identifier
            time (double): target time
        Returns:
            Returns requested field (Field).
        """
        fileName  = "paraview/MMPTestCase_v1.case"
        self.reader.readEnsightFile(fileName )
        if (self.mesh == None):
            self.mesh = self.reader.getMesh((12,))
        if (fieldID == FieldID.FID_Temperature):
            fieldName = "TEMPERATURE"
        else:
            print ("error: no fieldName specified")
        return self.reader.getField(self.mesh, fileName, fieldName, False, (12,))
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1


