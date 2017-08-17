import sys
sys.path.append('.')
sys.path.append('..')
sys.path.append('../..')

from mupif import *

def generateBackgroundMesh (nx, ny, lx, ly, origin):
    """
    Generates mesh on rectangular domain in x-y plane, z coordinates equal to 0.
    The cells used are quadratic triangles. 
    
    :param int nx: number of vertices in x direction (odd number)
    :param int ny: number of vertices in y direction (odd number)
    :param double lx: length of edge in x-direction
    :param double ly: length of edge in y-direction
    :param tuple origin: coordinates(double) of lower left corner
    
    :return: mesh with nodes defined on a 2D plane
    :rtype: Mesh.UnstructuredMesh
    
    """
    
    # compute nodal point spacing
    dx = lx/(nx-1)
    dy = ly/(ny-1)

    mesh = Mesh.UnstructuredMesh()
    #generate nodes first
    nodes = []
    num = 0
    for i in range (nx):
        for j in range (ny):
            vertex = Vertex.Vertex(num, num, coords=(origin[0]+i*dx, origin[1]+j*dy, origin[2]))
            nodes.append(vertex)
            num += 1
    #generate cells
    cells = []
    num=1
    for i in range(nx/2):
        for j in range(ny/2):
            # index of lower left node
            si = j*(nx*2)+i*2
            #elem = Cell.Triangle_2d_quad (mesh, num, num, vertices=(si,si+10,si+2,si+5,si+6,si+1))
            elem = Cell.Triangle_2d_quad (mesh, num, num, vertices=(si,si+(2*ny),si+2,si+ny,si+ny+1,si+1))
            cells.append(elem)
            num+=1
            #elem = Cell.Triangle_2d_quad (mesh, num, num, vertices=(si+10,si+12,si+2,si+11,si+7,si+6))
            elem = Cell.Triangle_2d_quad (mesh, num, num, vertices=(si+(2*ny),si+(2*ny)+2,si+2,si+(2*ny)+1,si+ny+2,si+ny+1))
            cells.append(elem)
            num+=1
    mesh.setup(nodes, cells)
    return mesh



if __name__ == "__main__":
    m = generateBackgroundMesh(5,5,0.03, 0.03, (-0.015, -0.015, 0.0))
    #generate sample linear field
    values=[]
    for i in range(5):
        for j in range(5):
            values.append((1.0*i*j,))
    f = Field.Field(m, FieldID.FID_Displacement, ValueType.Scalar, 'm', 0.0, values)
    #check
    v=f.evaluate((0.01,0.01,0))
    print (v)
    f.field2VTKData().tofile('test')
    
