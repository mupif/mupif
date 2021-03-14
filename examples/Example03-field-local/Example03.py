#!/usr/bin/env python
import sys
import logging
import tempfile
sys.path.append('../..')
import mupif as mp

log = logging.getLogger()


def main():

    # generate field and corresponding mesh
    msh = mp.UnstructuredMesh()
    vertices = []
    values1 = []
    values2 = []
    num = 0
    for i in range(40):
        for j in range(15):
            vertices.append(mp.Vertex(number=(i*15)+j, label=(i*15)+j+1, coords=(float(i), float(j), 0.0)))
            values1.append((num,))
            num += 0.5
    cells = []
    num = 0
    for i in range(39):
        for j in range(14):
            cells.append(mp.Quad_2d_lin(mesh=msh, number=num, label=num, vertices=((i*15)+j, (i+1)*15+j, (i+1)*15+j+1, ((i*15)+j+1))))
            values2.append((num,))
            num += 1

    msh.setup(vertices, cells)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Check saving a mesh
        msh.dumpToLocalFile(tmpdir+'/mesh.dat')
        mp.Mesh.loadFromLocalFile(tmpdir+'/mesh.dat')

    # field1 is vertex based, i.e., field values are provided at vertices
    field1 = mp.Field(mesh=msh, fieldID=mp.FieldID.FID_Temperature, valueType=mp.ValueType.Scalar, unit=mp.U.K, time=1.*mp.Q.s, value=values1)
    # field1.field2Image2D(title='Field', barFormatNum='%.0f')
    # field2 is cell based, i.e., field values are provided for cells
    field2 = mp.Field(
        mesh=msh, fieldID=mp.FieldID.FID_Temperature, valueType=mp.ValueType.Scalar, unit=mp.U.K, time=1.*mp.Q.s, value=values2, fieldType=mp.FieldType.FT_cellBased
    )

    # evaluate field at given point
    position = (20.1, 7.5, 0.0)
    value1 = field1.evaluate(position)  # correct answer 154.5
    log.debug("Field1 value at position "+str(position)+" is "+str(value1))
    position = (20.1, 8.5, 0.0)
    value2 = field2.evaluate(position)  # correct answer 287.0
    log.debug("Field2 value at position "+str(position)+" is "+str(value2))

    field1.toMeshioMesh().write('example1.vtk')
    field2.toMeshioMesh().write('example2.vtk')

    # Test pickle module - serialization
    field1.dumpToLocalFile('field.dat')
    field3 = mp.Field.loadFromLocalFile('field.dat')
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
