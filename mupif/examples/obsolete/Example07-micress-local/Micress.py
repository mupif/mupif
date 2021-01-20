import sys
sys.path.append('../../..')
sys.path.append('.')
from mupif import VtkReader2
from mupif import Model
from mupif import FieldID
import pyvtk
import logging
log = logging.getLogger()

import mupif.physics.physicalquantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])
##
vtkreader2.pyvtk_monkeypatch()


class Micress(model.Model):

    def __init__ (self, file):
        super(Micress, self).__init__(file)
        self.mesh = None
        super(Micress, self).__init__(file)

    def getField(self, fieldID, time):
        Data = pyvtk.VtkData('micress/sim.vtk')
        log.debug(Data.header)

        dim=[]
        dim=Data.structure.dimensions
        log.debug(dim)

        #Number of nodes in each direction
        nx=dim[0]
        ny=dim[1]
        nz=dim[2]

        #coordinates of the points
        coords=[]
        coords= Data.structure.get_points()

        numNodes = Data.point_data.length
        log.debug(numNodes)

        if (self.mesh == None):
            self.mesh = vtkreader2.readMesh(numNodes,nx,ny,nz,coords)

        f = vtkreader2.readField(self.mesh, Data,FieldID.FID_Concentration, PQ.getDimensionlessUnit(), timeUnits, "conc1", "micress/sim.vtk", 1)
        return f

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1,'s')

