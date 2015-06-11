
import sys
sys.path.append('../..')
sys.path.append('.')
from mupif import VtkReader2
from mupif import Application
import pyvtk


class Micress(Application.Application):

    def __init__ (self, file):
        self.mesh = None
        super(Micress, self).__init__(file)

    def getField(self, fieldID, time):
        Data = pyvtk.VtkData('micress/sim.vtk')
        print Data.header

        dim=[]
        dim=Data.structure.dimensions
        print dim

        #Number of nodes in each direction
        nx=dim[0]
        ny=dim[1]
        nz=dim[2]

        #coordinates of the points
        coords=[]
        coords= Data.structure.get_points()

        numNodes = Data.point_data.length
        print numNodes

        if (self.mesh == None):
            self.mesh = VtkReader2.readMesh(numNodes,nx,ny,nz,coords)

        f = VtkReader2.readField(self.mesh, Data,"conc1",1)
        return f

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1


