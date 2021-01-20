#!/usr/bin/env python
from builtins import range
#
# This example requires pyvtk module, install it using
# pip install pyvtk
# Note: pyvtk is only available in Python 2.x (Sept, 2014)
#
import sys
import logging
sys.path.append('../../..')
from mupif import *
import mupif
import mupif.physics.physicalquantities as PQ

log = logging.getLogger()
temperatureUnit = PQ.PhysicalUnit('K', 1., [0, 0, 0, 0, 1, 0, 0, 0, 0])


def main():

    # generate field and corresponding mesh
    msh = mupif.mesh.UnstructuredMesh()
    vertices = []
    values1 = []
    values2 = []
    num = 0
    for i in range(40):
        for j in range(15):
            vertices.append(vertex.Vertex((i*15)+j, (i*15)+j+1, (float(i), float(j), 0.0)))
            values1.append((num,))
            num += 0.5
    cells = []
    num = 0
    for i in range(39):
        for j in range(14):
            cells.append(cell.Quad_2d_lin(msh, num, num, ((i*15)+j, (i+1)*15+j, (i+1)*15+j+1, ((i*15)+j+1))))
            values2.append((num,))
            num += 1

    msh.setup(vertices, cells)

    # Check saving a mesh
    msh.dumpToLocalFile('mesh.dat')
    mupif.mesh.Mesh.loadFromLocalFile('mesh.dat')

    time = PQ.PhysicalQuantity(1.0, 's')
    # field1 is vertex based, i.e., field values are provided at vertices
    field1 = field.Field(msh, FieldID.FID_Temperature, ValueType.Scalar, temperatureUnit, time, values1)
    # field1.field2Image2D(title='Field', barFormatNum='%.0f')
    # field2 is cell based, i.e., field values are provided for cells
    field2 = field.Field(
        msh, FieldID.FID_Temperature, ValueType.Scalar, temperatureUnit, time, values2, field.FieldType.FT_cellBased)

    # evaluate field at given point
    position = (20.1, 7.5, 0.0)
    value1 = field1.evaluate(position)  # correct answer 154.5
    log.debug("Field1 value at position "+str(position)+" is "+str(value1))
    position = (20.1, 8.5, 0.0)
    value2 = field2.evaluate(position)  # correct answer 287.0
    log.debug("Field2 value at position "+str(position)+" is "+str(value2))

    field1.field2VTKData().tofile('example1')
    field2.field2VTKData().tofile('example2')

    # Test pickle module - serialization
    field1.dumpToLocalFile('field.dat')
    field3 = field.Field.loadFromLocalFile('field.dat')
    position = (20.1, 9.5, 0.0)
    value3 = field3.evaluate(position)  # correct answer 155.5

    if (abs(value1.getValue()[0]-154.5) <= 1.e-4) and (abs(value2.getValue()[0]-288.0) <= 1.e-4) and (abs(value3.getValue()[0]-155.5) <= 1.e-4):
        log.info("Test OK")
    else:
        log.error("Test FAILED")
        import sys
        sys.exit(1)


if __name__ == '__main__':
        main()
