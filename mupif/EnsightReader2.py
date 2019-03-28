# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#
from builtins import range

import re

from . import Mesh
from . import Vertex
from . import Cell
from . import BBox
from . import Field
from . import FieldID
from . import ValueType

debug = 0


def readEnsightGeo(name, partFilter, partRec):
    """
    Reads Ensight geometry file (Ensight6 format) and returns corresponding Mesh object instance. Supports only unstructured meshes.

    :param str name: Path to Ensight geometry file (\*.geo)
    :param tuple partFilter: Only parts with id contained in partFiler will be imported
    :param list partRec: A list containing info about individual parts (number of elements). Needed by readEnsightField
    :return: mesh
    :rtype: Mesh.Mesh
    """
    vertexMapping = {}
    vertices = []
    cells = []
    vnum = 0
    enum = 0

    # open the geo file
    f = open(name, 'r')
    if debug: 
        print("Importing geometry from %s" % name)

    mesh = Mesh.UnstructuredMesh()

    # process header (6 lines)
    desc1 = f.readline()
    desc2 = f.readline()
    nodeidrec = f.readline()
    # check if nodal ids given -> required
    if not re.match('node\s+id\s+given', nodeidrec):
        print("Given node ids required")
        return

    elemidrec = f.readline()
    # check if element ids given -> required
    if not re.match('element\s+id\s+given', elemidrec):
        print("Given element ids required")
        return
    coordkwdrec = f.readline()
    numberOfUnstructuredNodes = int(f.readline())
    # check
    # read unstructured coordinates
    for i in range(numberOfUnstructuredNodes):
        line = f.readline()
        match = re.match('(.{8})(.{12})(.{12})(.{12})', line)
        # print line
        if match:
            id = int(match.group(1))
            x = float(match.group(2))
            y = float(match.group(3))
            z = float(match.group(4))
            # print id, x, y, z
            vertexMapping[id] = vnum  # remember mapping id -> vertex number
            vertices.append(Vertex.Vertex(vnum, id, (x, y, z)))
            # increment vertex counter
            vnum = vnum+1
    # read parts in sequential order
    line = f.readline()
    while line:
        match = re.search('\s*part\s+(\d+)', line)
        if match:
            partnum = int(match.group(1))
            partRec.append({})  # add empty dict for each part containing number of elements for each elemeet type
            if partnum in partFilter:
                if debug:
                    print("Importing part %d" % partnum)
                partdesc = f.readline().rstrip('\r\n')
                # process part 
                # get element type
                line = f.readline()
                (line, enum) = readEnsightGeo_Part(f, line, mesh, enum, cells, vertexMapping, partnum, partdesc, partRec)
            else:
                line = f.readline() 
        else:
            line = f.readline()

    if debug:
        print("Setting up mesh: %d vertices, %d cells" % (vnum, enum))
        print(len(vertices), len(cells))
    mesh.setup(vertices, cells)
    return mesh


def readEnsightGeo_Part(f, line, mesh, enum, cells, vertexMapping, partnum, partdesc, partRec):
    """
    Reads single cell part geometry from an Ensight file.

    :param File f: File object
    :param str line: Current line to process (should contain element type)
    :param Mesh.Mesh mesh: Mupif mesh object to accommodate new cells
    :param int enum: Accumulated cell number
    :param list cells: List of individual Cells
    :param dict vertexMapping: Map from vertex label (as given in Ensight file) to local number
    :param int partnum: Part number
    :param list partdesc: Partition description record
    :param list partRec: Output agrument (list) containing info about individual parts (number of elements). Needed by readEnsightField
    :return: tuple (line, cell number)
    :rtype: tuple (line, enum)
    """
    # if the next line is not next part record, then should be element section
    while not re.search('\s*part\s+(\d+)', line):
        if line == '':
            break
        # ok no "part" keyword, parse element section
        eltype = line.rstrip('\r\n')
        if debug: 
            print("(", eltype, ")")
        line = f.readline()
        nelem = int(line.rstrip('\r\n'))
        # remember info to partRec
        partRec[partnum-1][eltype] = nelem
        if debug:
            print("part %s nelem %d" % (partdesc, nelem))
        # read individual elements
        for i in range(nelem):
            elemRec = f.readline()
            if eltype == "hexa8":
                match = re.match('(.{8})(.{8})(.{8})(.{8})(.{8})(.{8})(.{8})(.{8})(.{8})', elemRec)
                if match:
                    elnum = int(match.group(1))
                    elnodes = (int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)), 
                               int(match.group(6)), int(match.group(7)), int(match.group(8)), int(match.group(9)))
                    # print ("Brick: %d (%d %d %d %d %d %d %d %d)"%(elnum, elnodes[0],elnodes[1],elnodes[2],elnodes[3],elnodes[4],elnodes[5],elnodes[6],elnodes[7]))
                    _vert = [vertexMapping[i] for i in elnodes]
                    cells.append(Cell.Brick_3d_lin(mesh, enum, enum, tuple(_vert)))
                    enum = enum+1
            elif eltype == "quad4":
                match = re.match('(.{8})(.{8})(.{8})(.{8})(.{8})', elemRec)
                if match:
                    elnum = int(match.group(1))
                    elnodes = (int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)))
                    if debug:
                        print("Quad: %d (%d %d %d %d)" % (elnum, elnodes[0], elnodes[1], elnodes[2], elnodes[3]))
                    _vert = [vertexMapping[i] for i in elnodes]
                    cells.append(Cell.Quad_2d_lin(mesh, enum, enum, tuple(_vert)))
                    enum = enum+1
            else:
                pass
                print("Element type %s not suported" % eltype)
        # finished parsing part for specific element type
        line = f.readline()
    # next part record found
    return line, enum

    
def readEnsightField(name, parts, partRec, type, fieldID, mesh, units, time):
    """
    Reads either Per-node or Per-element variable file and returns corresponding Field representation.

    :param str name: Input field name with variable data
    :param tuple parts: Only parts with id contained in partFiler will be imported
    :param list partRec: A list containing info about individual parts (number of elements per each element type).
    :param int type: Determines type of field values: type = 1 scalar, type = 3 vector, type = 6 tensor
    :param FieldID fieldID: Field type (displacement, strain, temperature ...)
    :param Mesh.Mesh mesh: Corresponding mesh
    :param PhysicalUnit units: field units
    :param PhysicalQuantity time: time
    :return: FieldID for unknowns
    :rtype: Field
    """
    vertexVals = []
    cellVals = []
    indx = list(range(6))
    values = []

    if type == 1:
        ftype = ValueType.Scalar
    elif type == 3:
        ftype = ValueType.Vector
    else:
        ftype = ValueType.Tensor

    # open the geo file
    f = open(name, 'r')

    # get variable name (1st line)
    varname = f.readline().rstrip('\r\n')
    if debug:
        print("Importing %s from %s" % (varname, name))
    
    # now check if nodal records available or part (cell records)
    line = f.readline()
    match = re.match('part\s+(\d+)', line)
    if not match:
        # nodal (vertex based specification)
        size = mesh.getNumberOfVertices() * type
        print("Expecting ", mesh.getNumberOfVertices(), " nodal records in ", size//6, " lines")
        # read nodeal variables
        for i in range(size//6):  # six values per row in fixed format 12.5e
            for j in indx:
                try:
                    vertexVals.append(float(line[j*12:(j+1)*12]))
                except:
                    print("exception....", j, line, ">", line[j*12:(j+1)*12])
            line = f.readline()
        
        # parse remaining values
        # line = f.readline()
        for j in range(size % 6):
            vertexVals.append(float(line[j*12:(j+1)*12]))
        if size % 6 > 0:
            line = f.readline()
        # done parsing nodal record(s)
        # so this should be per-vertex variable file -> vertex based field
        # convert vertexVals into form required by field 
        for i in range(mesh.getNumberOfVertices()):
            if type == 1:  # scalar
                values.append((vertexVals[i],))
            elif type == 3:  # vector
                values.append((vertexVals[i*3], vertexVals[i*3+1], vertexVals[i*3+2]))
            elif type == 6:  # tensor
                values.append((vertexVals[i*6], vertexVals[i*6+1], 
                               vertexVals[i*6+2], vertexVals[i*6+3],
                               vertexVals[i*6+4], vertexVals[i*6+4]))

        field = Field.Field(mesh, fieldID, ftype, units, time, values, Field.FieldType.FT_vertexBased)
        return field

    else:
        # ok nodal section missing, parts should provide per-cell variables
        while line:
            match = re.search('\s*part\s+(\d+)', line)
            if match:
                partnum = int(match.group(1))
                if partnum in parts:
                    if debug:
                        print("Importing part %d" % partnum)
                    # get element type
                    line = f.readline()
                    # if the next line is not next part record, then should be element section
                    while not re.search('\s*part\s+(\d+)', line):
                        # ok no "part" keyword, parse element section
                        eltype = line.rstrip('\r\n')
                        if debug:
                            print("eltype:", eltype)
                        nelem = partRec[partnum-1][eltype]  # get number of elements in part
                        if debug:
                            print("(", eltype, nelem, ")")
                        size = nelem * type
                        cellVals = []  # empty values for each element group
                        for i in range(size//6):  # six values per row in fixed format 12.5e
                            line = f.readline()
                            # print ".",
                            for j in indx:
                                cellVals.append(float(line[j*12:(j+1)*12]))
                        # parse remaining values
                        line = f.readline()
                        for j in range(size % 6):
                            cellVals.append(float(line[j*12:(j+1)*12]))
                        if size % 6 > 0:
                            line = f.readline()
                        # print "%"
                        # now convert that into format required by filed
                        for i in range(nelem):
                            if type == 1:  # scalar
                                values.append((cellVals[i],))
                            elif type == 3:  # vector
                                values.append((cellVals[i*3], cellVals[i*3+1], cellVals[i*3+2]))
                            elif type == 6:  # tensor
                                values.append((cellVals[i*6], cellVals[i*6+1], 
                                               cellVals[i*6+2], cellVals[i*6+3],
                                               cellVals[i*6+4], cellVals[i*6+4]))
                        if debug:
                            print("done importing element section")
                        # done parsing cell record(s) in part

                else:  # if (partnum in parts):   proceed to next part
                    line = f.readline()
            else:
                line = f.readline()
        # so this should be per-cell variable file -> cell based field
        field = Field.Field(mesh, fieldID, ftype, units, time, values, Field.FieldType.FT_cellBased)
        return field

