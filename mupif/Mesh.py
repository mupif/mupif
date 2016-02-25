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
from __future__ import print_function
from builtins import str, zip, range, object

from . import APIError
from . import Octree
from . import BBox
import copy
import time
import sys
import numpy
from . import CellGeometryType
try:
   import cPickle as pickle #faster serialization if available
except:
   import pickle

#enum to distinguish iterartors provided by domain
VERTICES=0; CELLS=1

#debug flag
debug = 0

class MeshIterator(object):
    """
    Class implementing iterator on Mesh components (vertices, cells).

    .. automethod:: __init__
    .. automethod:: __iter__
    .. automethod:: __next__
    """
    def __init__(self, mesh, type):
        """
        Constructor.

        :param Mesh mesh: Given mesh
        :param str type: Type of mesh, e.g. VERTICES or CELLS
        """
        if ((type == VERTICES) or (type == CELLS)):
            self.type = type
            self.mesh = mesh
        else:
            print ("Unsupported iterator type")
            abort(0)

    def __iter__(self):
        """
        :return: Itself
        :rtype: MeshIterator
        """
        self.i = 0
        return self

    def __next__(self):
        """
        :return: Returns next Mesh components.
        :rtype: MeshIterator
        """
        if self.type == VERTICES:
            if self.i+1 <= self.mesh.getNumberOfVertices():
                item = self.mesh.getVertex(self.i)
                self.i += 1
                return item
            else:
                raise StopIteration()

        elif self.type == CELLS:
            if self.i+1 <= self.mesh.getNumberOfCells():
                item = self.mesh.getCell(self.i)
                self.i += 1
                return item
            else:
                 raise StopIteration()
    # in py3k, this would lead to infinite recursion since 2to3 renames to __next__ already
    if sys.version_info[0]==2:
        def next (self):
            """
            Python 2.x compatibility, see :func:`MeshIterator.__next__`
            """
            return self.__next__()   #Python 2.x compatibility

class Mesh(object):
    """
    Abstract representation of a computational domain.
    Mesh contains computational cells and vertices.
    Derived classes represent structured, unstructured FE grids, FV grids, etc.

    Mesh is assumed to provide a suitable instance of cell and vertex localizers.

    .. automethod:: __init__
    """
    def __init__(self):
        self.mapping = None

    @classmethod
    def loadFromLocalFile(cls,fileName):
        """
        Alternative constructor which loads an instance from a Pickle module.

        :param str fileName: File name

        :return: Returns Mesh instance
        :rtype: Mesh
        """
        return pickle.load(file(fileName,'r'))

    def copy(self):
        """
        Returns a copy of the receiver.

        :return: A copy of the receiver
        :rtype: Copy of the receiver, e.g. Mesh

        .. Note:: DeepCopy will not work, as individual cells contain mesh link attributes, leading to underlying mesh duplication in every cell!
        """
    def getNumberOfVertices(self):
        """
        Get number of vertices (nodes).

        :return: Number of Vertices
        :rtype: int
        """
        return 0;

    def getNumberOfCells(self):
        """
        Return number of cells (finite elements).

        :return: The number of Cells
        :rtype: int
        """
        return 0;

    def getVertex(self, i):
        """
        Returns i-th vertex.

        :param int i: i-th vertex
        :return: vertex
        :rtype: Vertex
        """

    def getVertices(self):
        """
        Return all vertex coordinates as 2D (Nx3) numpy.array; each i-th row contains 3d coordinates of the i-th vertex.

        :return: vertices
        :rtype: numpy.array

        .. note:: This method has not been tested yet.
        """
        nv=self.getNumberOfVertices()
        ret=numpy.empty((nv,3),dtype=numpy.float)
        for i in range(0,nv):
            ret[i]=numpy.array(self.getVertex(i).getCoordinates())
        return ret

    def getCell(self, i):
        """
        Returns i-th cell.

        :param int i: i-th cell
        :return: cell
        :rtype: Cell
        """

    def getCells(self):
        """
        Return all cells as 2x numpy.array; each i-th row contains vertex indices for i-th cell. Does in 2 passes, first to determine maximum number of vertices per cell (to shape the field accordingly). For cells with less vertices than the maximum, excess ones are assigned the invalid value of -1.

        :return: (cell_types,cell_vertices)
        :rtype: (numpy.array,numpy.array)

        .. note:: This method has not been tested yet.
        """
        # determine the maximum number of vertices
        mnv=0
        nc=self.getNumberOfCells()
        for i in range(nc): mnv=max(mnv,self.getCell(i).getNumberOfVertices())
        tt,cc=numpy.empty(shape=(nc,),dtype=numpy.int),numpy.full(shape=(nc,mnv),fill_value=-1,dtype=numpy.int)
        for i in range(nc):
            c=self.getCell(i)
            tt[i]=c.getGeometryType()
            vv=numpy.array([v.getNumber() for v in c.getVertices()],dtype=numpy.int)
            cc[i,:len(vv)]=vv # excess elements in the row stay at -1
        return tt,cc

    def asHdf5Object(self,parentgroup,newgroup):
        def numpyHash(*args):
            'Return concatenated hash (hexdigest) of all args, which must be numpy arrays. This function is used to find an identical mesh which was already stored.'
            import hashlib
            return ''.join([hashlib.sha1(arr.view(numpy.uint8)).hexdigest() for arr in args])
        mvc,(mct,mci)=self.getVertices(),self.getCells()
        mhash='mesh_'+numpyHash(mvc,mct,mci)
        # try to find this mesh in the hdf5 group and return that one, instead of creating a new one
        if parentgroup:
            for name,group in parentgroup.items():
                if 'mhash' in group.attrs and group.attrs['mhash']==mhash: return parentgroup[name]
        gg=parentgroup.create_group(name=newgroup)
        for name,data in ('vertex_coords',mvc),('cell_types',mct),('cell_vertices',mci): gg[name]=data
        gg.attrs['mhash']=mhash
        gg.attrs['__class__']=self.__class__.__name__
        gg.attrs['__module__']=self.__class__.__module__
        return gg

    @staticmethod
    def makeFromHdf5Object(h5obj):
        """
        Create new :obj:`Mesh` instance from given hdf5 object.

        :return: new instance
        :rtype: :obj:`Mesh` or its subclass
        """
        # instantiate the right Mesh subclass
        klass=getattr(__import__(h5obj.attrs['__module__']),h5obj.attrs['__class__'])
        ret=klass()
        mvc,mct,mci=h5obj['vertex_coords'],h5obj['cell_types'],h5obj['cell_vertices']
        # construct vertices
        vertices=[Vertex(number=vi,label=None,coord=tuple(mvc[vi])) for vi in range(mvc.shape[0])]
        cells=[Cell.getClassForCellGeometryType(mct[ci])(mesh=ret,number=ci,label=None,vertices=tuple(mci[ci])) for ci in range(mct.shape[0])]
        ret.setup(vertexList=vertices,cellList=cells)
        return ret


    def getMapping(self):
        """
        Get mesh mapping.

        :return: The mapping associated to a mesh
        :rtype: defined by API
        """
        return self.mapping

    def vertexLabel2Number(self, label):
        """
        Returns local vertex number corresponding to given label. If no label found, throws an exception.

        :param str label: Vertex label
        :return: Vertex number
        :rtype: int
        :except: Label not found
        """

    def cellLabel2Number(self, label):
        """
        Returns local cell number corresponding to given label. If no label found, throws an exception.

        :param str label: Cell label
        :return: Cell number
        :rtype: int
        :except: Label not found
        """

    def vertices(self):
        """
        Iterator over vertices.
        
        :return: Iterator over vertices
        :rtype: MeshIterator
        """

        return MeshIterator(self, VERTICES) 

    def cells(self):
        """
        Iterator over cells.

        :return: Iterator over cells
        :rtype: MeshIterator
        """
        return MeshIterator(self, CELLS)

    def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
        """
        Dump Mesh to a file using a Pickle serialization module.

        :param str fileName: File name
        :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
        """
        pickle.dump(self, file(fileName,'w'), protocol)


class UnstructuredMesh(Mesh):
    """
    Represents unstructured mesh. Maintains the list of vertices and cells.

    The class contains:

    * vertexList: list of vertices
    * cellList: list of interpolation cells
    * vertexOctree: vertex spatial localizer
    * cellOctree: cell spatial localizer
    * vertexDict: vertex dictionary
    * cellDict: cell dictionary

    .. automethod:: __init__
    .. automethod:: __buildVertexLabelMap__
    .. automethod:: __buildCellLabelMap__
    """

    def __init__(self):
        """
        Constructor.
        """
        Mesh.__init__(self)
        self.vertexList = []
        self.cellList    = []
        self.vertexOctree = None
        self.cellOctree   = None
        #label2local_number maps
        self.vertexDict   = None
        self.cellDict     = None

    def setup (self, vertexList, cellList):
        """
        Initializes the receicer according to given vertex and cell lists.

        :param tuple vertexList: A tuple of vertices
        :param tuple cellList: A tuple of cells
        """
        self.vertexList = vertexList
        self.cellList = cellList

    def copy(self):
        """
        See :func:`Mesh.copy`
        """
        vertexList = []
        cellList   = []
        for i in self.vertices():
            vertexList.append(copy.deepcopy(v))
        for i in self.cells():
            cellList.append(i.copy())
        return UnstructuredMesh(vertexList,cellList)

    def __getstate__(self):
        '''Customized method returning dictionary for pickling.

        We don't want to pickle (and pass over the wire) cell and vertex localizers -- those may be based on c++ fastOctant, which the other side does not necessarily support.

        Therefore return ``__dict__`` (that's what pickle does in the absence of ``__getstate__``) but with ``vertexOctree`` and ``cellOctree`` set to ``None``.
        '''
        # shallow copy of __dict__
        d2=self.__dict__.copy()
        d2['vertexOctree']=d2['cellOctree']=None
        return d2

    def getNumberOfVertices(self):
        """
        See :func:`Mesh.getNumberOfVertices`
        """
        return len(self.vertexList)

    def getNumberOfCells(self):
        """
        See :func:`Mesh.getNumberOfCells`
        """
        return len(self.cellList)

    def getVertex(self, i):
        """
        See :func:`Mesh.getVertex`
        """
        return self.vertexList[i]

    def getCell(self, i):
        """
        See :func:`Mesh.getCell`
        """
        return self.cellList[i]

    def giveVertexLocalizer(self):
        """
        :return: Returns the vertex localizer.
        :rtype: Octree
        """
        if self.vertexOctree: 
            return self.vertexOctree
        else:
            # loop over vertices to get bounding box first

            # XXX: remove this
            if 0:
                init=True
                minc=[]
                maxc=[]
                for vertex in self.vertices():
                    if init:
                        for i in range(len(vertex.coords)):
                            minc[i]=maxc[i]=vertex.coords[i]
                    else:
                        for i in range(len(vertex.coords)):
                            minc[i]=min(minc[i], vertex.coords[i])
                            maxc[i]=max(maxc[i], vertex.coords[i])
            else:
                vvv=self.vertices()
                c0=vvv.__iter__().__next__().getCoordinates() # use the first bbox as base
                bb=BBox.BBox(c0,c0) # ope-pointed bbox
                for vert in vvv: bb.merge(vert.getCoordinates()) # extend it with all other cells
                minc,maxc=bb.coords_ll,bb.coords_ur

            #setup vertex localizer
            size = max ( y-x for x,y in zip (minc,maxc))
            mask = [(y-x)>0.0 for x,y in zip (minc,maxc)]
            self.vertexOctree = Octree.Octree(minc, size, mask) 
            if debug: 
                t0=time.clock()
                print ("Mesh: setting up vertex octree ...\nminc=", minc,"size:", size, "mask:",mask,"\n")
            # add mesh vertices into octree
            for vertex in self.vertices():
                self.vertexOctree.insert(vertex)
            if debug: print ("done in ", time.clock() - t0, "[s]")

            return self.vertexOctree

    def giveCellLocalizer(self):
        """
        Get the cell localizer.

        :return: Returns the cell localizer.
        :rtype: Octree
        """
        if debug: t0=time.clock()
        if self.cellOctree: 
            return self.cellOctree
        else:
            # loop over cell bboxes to get bounding box first
            if debug: print('Start at: ',time.clock()-t0)

            ## XXX: remove this
            if 0:
                init=True
                minc=[]
                maxc=[]
                for cell in self.cells():
                    #print "cell bbox:", cell.giveBBox()
                    if init:
                        minc = [c for c in cell.getBBox().coords_ll]
                        maxc = [c for c in cell.getBBox().coords_ur]
                        init=False
                    else:
                        for i in range(len(cell.getBBox().coords_ll)):
                            minc[i]=min(minc[i], cell.getBBox().coords_ll[i])
                            maxc[i]=max(maxc[i], cell.getBBox().coords_ur[i])
            else:
                ccc=self.cells()
                bb=ccc.__iter__().__next__().getBBox() # use the first bbox as base
                for cell in ccc: bb.merge(cell.getBBox()) # extend it with all other cells
                minc,maxc=bb.coords_ll,bb.coords_ur
            if debug: print('Cell bbox: ',time.clock()-t0)

        #setup vertex localizer
        size = max ( y-x for x,y in zip (minc,maxc))
        mask = [(y-x)>0.0 for x,y in zip (minc,maxc)]
        self.cellOctree = Octree.Octree(minc, size, mask) 
        if debug: print('Octree ctor: ',time.clock()-t0)
        if debug: 
            print ("Mesh: setting up vertex octree ...\nminc=", minc,"size:", size, "mask:",mask,"\n")
        for cell in self.cells():
            self.cellOctree.insert(cell)
        if debug: print ("done in ", time.clock() - t0, "[s]")
        return self.cellOctree

    def __buildVertexLabelMap__(self):
        """
        Create a custom dictionary between vertex's label and Vertex instance.
        """
        self.vertexDict = {}
        # loop over vertex lists in both meshes
        for v in range(len(self.vertexList)):
            if self.vertexList[v].label in self.vertexDict:
                if debug:
                    print ("UnstructuredMesh::buildVertexLabelMap: multiple entry detected, vertex label ",  self.vertexList[v].label)
            else:
                self.vertexDict[self.vertexList[v].label]=v

    def __buildCellLabelMap__(self):
        """
        Create a custom dictionary between cell's label and Cell instance.
        """
        self.cellDict = {}
        # loop over vertex lists in both meshes
        for v in range(len(self.cellList)):
            if self.cellList[v].label in self.cellDict:
                if debug:
                    print ("UnstructuredMesh::buildCellLabelMap: multiple entry detected, cell label ",  self.cellList[v].label)
            else:
                self.cellDict[self.cellList[v].label]=v


    def vertexLabel2Number(self, label):
        """
        See :func:`Mesh.vertexLabel2Number`
        """
        if (not self.vertexDict):
            self.__buildVertexLabelMap__()
        return self.vertexDict[label]


    def cellLabel2Number(self, label):
        """
        See :func:`Mesh.cellLabel2Number`
        """
        if (not self.cellDict):
            self.__buildCellLabelMap__()
        return self.cellDict[label]


    def merge (self, mesh):
        """
        Merges receiver with a given mesh. This is based on merging mesh entities (vertices, cells) based on their labels, as they refer to global IDs of each entity, that should be unique.

        The procedure used here is based on creating a dictionary for every componenet from both meshes, where the key is component label so that the entities with the same ID could be easily identified.

        :param Mesh mesh: Source mesh for merging
        """
        #build vertex2local reciver map first
        if (not self.vertexDict):
            self.__buildVertexLabelMap__()
        #
        #merge vertexLists
        #
        if debug: print ("UnstructuredMesh::merge: merged vertices with label:")
        for v in mesh.vertices():
            if v.label in self.vertexDict:
                if debug:
                    print (v.label)
            else:
                indx=len(self.vertexList)
                self.vertexList[indx:]=[copy.deepcopy(v)]
                self.vertexDict[v.label]=indx

        # renumber vertexDict verices 
        number=0
        for v in self.vertexList:
            v.number = number
            number = number+1
        #
        # now merge cell lists
        #

        if (not self.cellDict):
            self.__buildCellLabelMap__()

        if debug: print ("UnstructuredMesh::merge: merged cells with label:")
        for c in mesh.cells():
            if c.label in self.cellDict:
                if debug:
                    print (c.label)
            else:
                # update c vertex list according to new numbering
                updatedVertices=[]
                for v in c.giveVertices():
                    updatedVertices.append(self.vertexDict[mesh.giveVertex(v).label])
                ccopy=c.copy()
                ccopy.vertices=tuple(updatedVertices)
                ccopy.mesh=self
                indx=len(self.cellList)
                self.cellList[indx:]=[ccopy]
                self.cellDict[ccopy.label]=indx
        print ()
        #last step: invalidate receiver 
        self.vertexOctree = None
        self.cellOctree = None

    def getVTKRepresentation (self):
        """
        Get VTK representatnion of the mesh.

        return: VTK representation of the receiver. Requires pyvtk module.
        :rtype: pyvtk.UnstructuredGrid
        """
        import pyvtk

        vertices = []
        hexahedrons = []
        tetrahedrons= []
        quads = []
        triangles = []

        #loop over receiver vertices and create list of vertex coordinates 
        for v in range(len(self.vertexList)):
            vertices.append(self.vertexList[v].coords)
        #loop over receiver cells 
        for c in range(len(self.cellList)):
            cell = self.cellList[c]
            cgt = cell.getGeometryType()
            if (cgt == CellGeometryType.CGT_TRIANGLE_1):
                triangles.append(cell.vertices)
            elif (cgt == CellGeometryType.CGT_QUAD):
                quads.append(cell.vertices)
            elif (cgt == CellGeometryType.CGT_TETRA):
                tetrahedrons.append(cell.vertices)
            elif (cgt == CellGeometryType.CGT_HEXAHEDRON):
                hexahedrons.append(cell.vertices)
            elif (cgt == CellGeometryType.CGT_TRIANGLE_2):
               # no direct support in pyvtk. map it to linear tringles
               triangles.append((cell.vertices[0], cell.vertices[3], cell.vertices[5]))
               triangles.append((cell.vertices[1], cell.vertices[4], cell.vertices[3]))
               triangles.append((cell.vertices[2], cell.vertices[5], cell.vertices[4]))
               triangles.append((cell.vertices[3], cell.vertices[4], cell.vertices[5]))
            else:
                msg = "Unsupported cell geometry type encountered: "+str(cgt)
                raise APIError.APIError (msg) 

        return pyvtk.UnstructuredGrid(vertices, hexahedron=hexahedrons, tetra=tetrahedrons, quad=quads, triangle=triangles)


