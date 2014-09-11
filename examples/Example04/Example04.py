#!/usr/bin/env python

#
# This example reequires pyvtk module, install it using
# pip install pyvtk
#

import sys
sys.path.append('../..')

from mupif import Field
from mupif import FieldID
from mupif import ValueType

from mupif import Mesh
from mupif import Vertex
from mupif import Cell
from mupif import BBox

def main():

    # generate field and corresponding mesh
    mesh = Mesh.UnstructuredMesh()
    vertices=[]
    values = []
    for i in range(40):
        for j in range (15):
            vertices.append(Vertex.Vertex((i*15)+j,(i*15)+j+1, (float(i),float(j),0.0)))
            values.append((i,))
    cells = []
    num=0
    for i in range(39):
        for j in range (14):
            cells.append(Cell.Quad_2d_lin(mesh, num, num, ((i*15)+j, (i+1)*15+j, (i+1)*15+j+1, ((i*15)+j+1))))
            num=num+1

    mesh.setup(vertices, cells)
    field = Field.Field(mesh, FieldID.FID_Temperature, ValueType.Scalar, None, None, values)

    # evaluate field at given point
    position=(20., 7.5, 0.0)
    value=field.evaluate(position)
    print "Field value at position ", position, " is ", value

    field.field2VTKData().tofile('example')
    



if __name__ == '__main__':
        main()
