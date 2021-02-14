

#from . import mesh
import mupif.mesh
from . import vertex
from . import cell
from . import field
from . import ValueType

from pyvtk.Scalars import Scalars
from pyvtk.PolyData import PolyData
from pyvtk import common

# debug flag
debug = 0


def readMesh(numNodes,nx,ny,nz,coords):
    """
    Reads structured 3D mesh

    :param int numNodes: Number of nodes
    :param int nx: Number of elements in x direction
    :param int ny: Number of elements in y direction
    :param int nz: Number of elements in z direction
    :param tuple coords: Coordinates for each nodes
    :return: Mesh
    :rtype: Mesh
    """
    mesh = mupif.mesh.UnstructuredMesh()
    vertices = []
    cells = []

    for i in range(0, numNodes):
        (x, y, z) = coords[i]
        # print (x,y,z)
        vertices.append(vertex.Vertex(i, i+1, (x, y, z)))

    print(numNodes)

    numElts = (nx-1)*(ny-1)*(nz-1)
    print(numElts)

    print("nx: ", nx)
    print("ny: ", ny)
    print("nz: ", nz)

    for e in range(0, numElts):
        # print "elem :",e
        i = e % (nx-1)
        # print "ligne i :", i
        j = (e//(nx-1)) % (ny-1)
        # print "col j :", j
        k = e//((nx-1)*(ny-1)) 
        # print "k :", k

        n1 = i + j*nx + k*nx*ny
        n2 = n1+1
        n3 = i + (j+1)*nx + k*nx*ny
        n4 = n3+1
        n5 = i + j*nx + (k+1)*nx*ny
        n6 = n5+1
        n7 = i + (j+1)*nx + (k+1)*nx*ny
        n8 = n7+1

        # print "n1 :", n1
        # print "n2 :", n2
        # print "n3 :", n3
        # print "n4 :", n4
        # print "n5 :", n5
        # print "n6 :", n6
        # print "n7 :", n7
        # print "n8 :", n8
        cells.append(cell.Brick_3d_lin(mesh, e, e+1, (n1, n2, n4, n3, n5, n6, n8, n7)))

    mesh.setup(vertices, cells)
    return mesh


def readField(mesh, Data, fieldID, units, time, name, filename, type):
    """
    :param mesh.Mesh mesh: Source mesh
    :param vtkData Data: vtkData obtained by pyvtk
    :param FieldID fieldID: Field type (displacement, strain, temperature ...)
    :param PhysicalUnit units: field units
    :param PhysicalQuantity time: time
    :param str name: name of the field to visualize
    :param str filename:
    :param int type: type of value of the field (1:Scalar, 3:Vector, 6:Tensor) 

    :return: Field of unknowns
    :rtype: Field
    """
    values = []

    if type == 1:
        ftype = ValueType.Scalar
    elif type == 3:
        ftype = ValueType.Vector
    else:
        ftype = ValueType.Tensor

    f = open(filename, "r")
    numScalars = 0
    for line in f.readlines():
        if line.find('SCALARS') >= 0:
            numScalars = numScalars+1
    print("numScalars : ",  numScalars)

    indice = None
    count = 0
    for i in range(0, numScalars):
        Name = Data.point_data.data[i].name
        if Name == name:
            indice = count
        count = count+1

    fieldName = Data.point_data.data[indice].name
    print("fieldName : ", fieldName)

    scalar = Data.point_data.data[indice].scalars

    numNodes = Data.point_data.length

    # for i in range(0,numNodes):
    #     print scalar[i]

    print("name : ", name)
    if name == fieldName:
        for i in range(0, numNodes):
            values.append((scalar[i],))
            # print "values : ", values

    field = field.Field(mesh, fieldID, ftype, units, time, values, field.FieldType.FT_vertexBased)
    return field


# #
# # The rest is to work around ambiguous legacy VTK format specification
# # which leads to errors in the strict implementation (pyvtk), as described
# # in https://github.com/pearu/pyvtk/wiki/unexpectedEOF
# #
# # Monkey-patches are not applied automatically, the user has to call
# # mupif.vtkreader2.pyvtk_monkeypatch() (can be made the default if useful).
# #
# # Works for both python 2.x and 3.x (adapted from fghorow-pyvtk-python3-port)
# #
# # Long-term solution is to patch upstream, and select behavior
# # split(' ') vs. split() based on some switch like pyvtk.permissive=True.
# #
# #


def patched_scalars_fromfile(f, n, sl):
    dataname = sl[0]
    datatype = sl[1].lower()
    assert datatype in ['bit', 'unsigned_char', 'char', 'unsigned_short', 'short', 'unsigned_int', 'int', 'unsigned_long', 'long', 'float', 'double'], repr(datatype)
    if len(sl) > 2:
        numcomp = eval(sl[2])
    else:
        numcomp = 1
    l = common._getline(f)
    l = l.split()
    assert len(l) == 2 and l[0].lower().decode('UTF-8') == 'lookup_table'
    tablename = l[1].decode('UTF-8')
    scalars = []
    while len(scalars) < n:
        scalars += list(map(eval, common._getline(f).split()))
    assert len(scalars) == n
    return Scalars(scalars, dataname, tablename)


def patched_polydata_fromfile(f, self):
    """Use VtkData(<filename>)."""
    points = []
    vertices = []
    lines = []
    polygons = []
    triangle_strips = []
    l = common._getline(f)
    k, n, datatype = [s.strip().lower() for s in l.split()]
    if k != 'points':
        raise ValueError('expected points but got %s' % (repr(k)))
    n = eval(n)
    assert datatype in ['bit', 'unsigned_char', 'char', 'unsigned_short', 'short', 'unsigned_int', 'int', 'unsigned_long', 'long', 'float', 'double'], repr(datatype)

    self.message('\tgetting %s points' % n)
    while len(points) < 3*n:
        l = common._getline(f)
        points += list(map(eval, l.split()))
    assert len(points) == 3*n
    while 1:
        l = common._getline(f)
        if l is None:
            break
        sl = l.split()
        k = sl[0].strip().lower()
        if k not in ['vertices', 'lines', 'polygons', 'triangle_strips']:
            break
        assert len(sl) == 3
        n, size = list(map(eval, [sl[1], sl[2]]))
        lst = []
        while len(lst) < size:
            l = common._getline(f)
            lst += list(map(eval, l.split()))
        assert len(lst) == size
        lst2 = []
        j = 0
        for i in range(n):
            lst2.append(lst[j+1:j+lst[j]+1])
            j += lst[j]+1
        exec('%s = lst2' % k)
    return PolyData(points, vertices, lines, polygons, triangle_strips), l


def pyvtk_monkeypatch():
    'Apply monkey-patches to work around https://github.com/pearu/pyvtk/wiki/unexpectedEOF in pyvtk without changing the source code.'
    print('Monkey-patching pyVTK, see https://github.com/pearu/pyvtk/wiki/unexpectedEOF for details.')
    import pyvtk.PolyData
    # pyVTK 0.4.x
    pyvtk.scalars_fromfile = patched_scalars_fromfile
    polydata_fromfile = patched_polydata_fromfile
    # PyVTK >= 0.5
    if hasattr(pyvtk, 'parsers'):
        pyvtk.parsers['scalars'] = patched_scalars_fromfile
        pyvtk.parsers['polydata'] = patched_polydata_fromfile




