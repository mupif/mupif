from __future__ import print_function, division
from builtins import range


from . import Mesh
from . import Vertex
from . import Cell
from . import Field
from . import FieldID
from . import ValueType

#debug flag
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
    mesh = Mesh.UnstructuredMesh()
    vertices = []
    cells = []

    for i in range(0,numNodes):
        (x,y,z) = coords[i]
        #print (x,y,z)
        vertices.append(Vertex.Vertex(i, i+1, (x,y,z)))

    print(numNodes)

    numElts = (nx-1)*(ny-1)*(nz-1)
    print(numElts)

    print("nx: ",nx)
    print("ny: ",ny)
    print("nz: ",nz)

    for e in range(0,numElts):
        #print "elem :",e
        i = e % (nx-1)
        #print "ligne i :", i
        j = (e//(nx-1))%(ny-1) 
        #print "col j :", j
        k = e//((nx-1)*(ny-1)) 
        #print "k :", k

        n1=i + j*nx + k*nx*ny
        n2=n1+1
        n3=i + (j+1)*nx + k*nx*ny
        n4=n3+1
        n5=i + j*nx + (k+1)*nx*ny
        n6=n5+1
        n7=i + (j+1)*nx + (k+1)*nx*ny
        n8=n7+1

        # print "n1 :", n1
        # print "n2 :", n2
        # print "n3 :", n3
        # print "n4 :", n4
        # print "n5 :", n5
        # print "n6 :", n6
        # print "n7 :", n7
        # print "n8 :", n8
        cells.append(Cell.Brick_3d_lin(mesh, e, e+1, (n1,n2,n4,n3,n5,n6,n8,n7)))

    mesh.setup(vertices, cells)
    return mesh

def readField(mesh, Data, fieldID, name, filename, type):
    """
    :param Mesh mesh: Source mesh
    :param vtkData Data: vtkData obtained by pyvtk
    :param FieldID fieldID: Field type (displacement, strain, temperature ...)
    :param str name: name of the field to visualize
    :param int type: type of value of the field (1:Scalar, 3:Vector, 6:Tensor) 
    :return: Field of unknowns
    :rtype: Field
    """
    values=[]

    if (type == 1):
        ftype = ValueType.Scalar
    elif (type == 3):
        ftype = ValueType.Vector
    else:
        ftype = ValueType.Tensor


    f=open(filename, "r")
    numScalars=0
    for line in f.readlines():
        if line.find('SCALARS')>= 0:
            numScalars=numScalars+1
    print("numScalars : ",  numScalars)

    count=0
    for i in range(0,numScalars):
        Name=Data.point_data.data[i].name
        if (Name==name):
            indice = count
        count=count+1

    fieldName=Data.point_data.data[indice].name
    print("fieldName : ", fieldName)

    scalar=[]
    scalar=Data.point_data.data[indice].scalars

    numNodes = Data.point_data.length

    # for i in range(0,numNodes):
    #     print scalar[i]

    print("name : ", name)
    if(name==fieldName):
        for i in range(0,numNodes):
            values.append((scalar[i],))
            #print "values : ", values

    field = Field.Field(mesh, fieldID ,ftype, None, None, values, Field.FieldType.FT_vertexBased )
    return field
