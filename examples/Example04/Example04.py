#!/usr/bin/env python

#
# This example reequires pyvtk module, install it using
# pip install pyvtk
# Note: pyvtk is only available in Python 2.x (Sept, 2014)
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
    values1 = []
    values2 = []
    for i in range(40):
        for j in range (15):
            vertices.append(Vertex.Vertex((i*15)+j,(i*15)+j+1, (float(i),float(j),0.0)))
            values1.append((i,))
    cells = []
    num=0
    for i in range(39):
        for j in range (14):
            cells.append(Cell.Quad_2d_lin(mesh, num, num, ((i*15)+j, (i+1)*15+j, (i+1)*15+j+1, ((i*15)+j+1))))
            values2.append((num,))
            num=num+1

    mesh.setup(vertices, cells)
    # field1 is vertex based, i.e., field values are provided at vertices
    field1 = Field.Field(mesh, FieldID.FID_Temperature, ValueType.Scalar, None, None, values1)
    # field1 is cell based, i.e., field values are provided for cells
    field2 = Field.Field(mesh, FieldID.FID_Temperature, ValueType.Scalar, None, None, values2, Field.FieldType.FT_cellBased)

    # evaluate field at given point
    position=(20., 7.5, 0.0)
    value=field1.evaluate(position)
    print ("Field1 value at position ", position, " is ", value)
    position=(20., 7.5, 0.0)
    value=field2.evaluate(position)
    print ("Field2 value at position ", position, " is ", value)

    field1.field2VTKData().tofile('example1')
    field2.field2VTKData().tofile('example2')
    



if __name__ == '__main__':
        main()
