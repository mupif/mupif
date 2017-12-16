
import sys
sys.path.append('../../..')
from mupif import *

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])
temperatureUnits = PQ.PhysicalUnit('K',   1.,    [0,0,0,0,1,0,0,0,0])

class Celsian(Application.Application):

    def __init__ (self, file):
        super(Celsian, self).__init__(file)
        self.mesh = None

    def getField(self, fieldID, time):
        parts=[1, 2]
        partRec=[]
        if (self.mesh == None):
            self.mesh = EnsightReader2.readEnsightGeo('paraview/MMPTestCase_v1.geo', parts, partRec)

        f = EnsightReader2.readEnsightField('paraview/fld_TEMPERATURE.escl', parts, partRec, 1, FieldID.FID_Temperature, self.mesh, temperatureUnits, time)
        return f

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1,'s')
    def getAssemblyTime(self, tstep):
        return tstep.getTime()


