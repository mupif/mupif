import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
from mupif import VtkReader2
import pyvtk




class VtkReader2_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_ReadMesh(self):
        m = VtkReader2.readMesh(8, 2, 2, 2, ((0., 0., 0.), (1., 0., 0.),(1., 1., 0.),(0., 1., 0.),(0., 0., 1.), (1., 0., 1.),(1., 1., 1.),(0., 1., 1.)))
        nV = m.getNumberOfVertices()
        nC = m.getNumberOfCells()

        self.assertTrue(nV == 8)
        self.assertTrue(nC == 1)

    def test_ReadField(self):
        Data = pyvtk.VtkData('./testVtkReader2.vtk')

        dim=[]
        dim=Data.structure.dimensions
        #Number of nodes in each direction
        nx=dim[0]
        ny=dim[1]
        nz=dim[2]
        #coordinates of the points
        coords=[]
        coords= Data.structure.get_points()
        #numNodes = Data.point_data.length
        numNodes = len(coords)
        mesh = VtkReader2.readMesh(numNodes,nx,ny,nz,coords)

        fc = VtkReader2.readField(mesh, Data,FieldID.FID_Concentration, Physics.PhysicalQuantities.getDimensionlessUnit(), "s", "conc", "testVtkReader2.vtk", 1)
        self.assertTrue(fc.fieldID == FieldID.FID_Concentration)
        self.assertTrue(fc.fieldType == Field.FieldType.FT_vertexBased)


    # python test_Cell.py for stand-alone test being run
if __name__ == '__main__': unittest.main()


