import mupif.mesh
from mupif import cell
from mupif import vertex
import numpy as np

# debug flag
debug = 0


def meshgen(origin, size, nx, ny, tria=False):
    """
    Generates a simple mesh on rectangular domain
    Params:
      origin(tuple): x,y coordinates of origin (lower left corner)
      size(tuple): tuple containing size in x and y directions
      nx(int): number of elements in x direction
      ny(int): number of elements in y direction
      tria(bool): when True, triangular mesh generated, quad otherwise
    """
    dx = size[0] / nx
    dy = size[1] / ny

    num = 0
    vertexlist = []
    celllist = []

    mesh = mupif.mesh.UnstructuredMesh()
    # generate vertices
    for ix in range(nx + 1):
        for iy in range(ny + 1):
            if debug:
                print("Adding vertex %d: %f %f %f " % (num, ix * dx, iy * dy, 0.0))
            vertexlist.append(
                vertex.Vertex(number=num, label=num, coords=(origin[0] + 1.0 * ix * dx, origin[1] + 1.0 * iy * dy, 0.0)))
            num = num + 1

    # generate cells
    num = 1
    for ix in range(nx):
        for iy in range(ny):
            si = iy + ix * (ny + 1)  # index of lower left node
            if not tria:
                if debug:
                    print("Adding quad %d: %d %d %d %d" % (num, si, si + ny + 1, si + ny + 2, si + 1))
                celllist.append(cell.Quad_2d_lin(mesh=mesh, number=num, label=num, vertices=(si, si + ny + 1, si + ny + 2, si + 1)))
                num = num + 1
            else:
                if debug:
                    print("Adding tria %d: %d %d %d" % (num, si, si + ny + 1, si + ny + 2))
                celllist.append(cell.Triangle_2d_lin(mesh=mesh, number=num, label=num, vertices=(si, si + ny + 1, si + ny + 2)))
                num = num + 1
                if debug:
                    print("Adding tria %d: %d %d %d" % (num, si, si + ny + 2, si + 1))
                celllist.append(cell.Triangle_2d_lin(mesh=mesh, number=num, label=num, vertices=(si, si + ny + 2, si + 1)))
                num = num + 1

    mesh.setup(vertexlist, celllist)
    return mesh

def make_meshio_box_hexa(dim=(1,1,1),sz=.1,):
    xx,yy,zz=[np.linspace(start=0,stop=dim[i],num=int(np.round((dim[i]-0)//sz)+1)) for i in (0,1,2)]
    sx,sy,sz=len(xx),len(yy),len(zz)
    syz=sx*sz
    X,Y,Z=np.meshgrid(xx,yy,zz)
    cells=[]
    for i in range(sx*sy*sz):
        if (i+1)%sz==0: continue
        if ((i//sz)+1)%sx==0: continue
        if ((i//syz)+1)%sy==0: continue
        lo,hi=[(o,o+1,o+sz+1,o+sz) for o in (i,i+syz)]
        cells.append((*lo,*hi))
    pts=np.column_stack((X.ravel(),Y.ravel(),Z.ravel()))
    import meshio
    return meshio.Mesh(points=pts,cells={'hexahedron':cells})
