# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
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

import Octree
import copy
import time

#enum to distinguish iterartors provided by domain
VERTICES=0; CELLS=1

#debug flag
debug = 0

class MeshIterator:
    """
    Class implementing iterator on Mesh components (vertices, cells).
    """
    def __init__(self, mesh, type):
        if ((type == VERTICES) or (type == CELLS)):
            self.type = type
            self.mesh = mesh
        else:
            print "Unsupported iterator type"
            abort(0)

    def __iter__(self):
        self.i = 0
        return self

    def next(self):
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

class Mesh:
    """
    Abstract representation of a computational domain.
    Described using computational cells and vertices, determining the cell geometry.
    Derived classes represent structured, unstructured FE grids, FV grids, etc.

    Mesh is assumed to provide a suitable instance of cell and vertex localizers.
    """
    def __init__(self):
        self.mapping = None

    def copy(self):
        """
        This will return a copy of the receiver. 
        NOTE: 
            DeepCopy will not work, as individual cells contain mesh link attributes, 
            leading to underlying mesh duplication in every cell!
        Returns:
            Copy of receiver (Mesh)
        """
    def getNumberOfVertices(self):
        """Returns the number of Vertices."""
        return 0;

    def getNumberOfCells(self):
        """Returns the number of Cells."""
        return 0;
        
    def getVertex(self, i):
        """
        Returns i-th vertex.
        Returns:
             vertex (Vertex)
        """

    def getCell(self, i):
        """
        Returns i-th cell.
        Returns:
             cell (Cell)
        """
        
    def getMapping(self):
        """Returns the mapping associated to mesh."""
        return self.mapping

    def vertexLabel2Number(self, label):
        """
        Returns local vertex number corresponding to given label.
        If no label corresponds, throws an exception
        Returns:
           vertex number (int)
        """
        
    def cellLabel2Number(self, label):
        """
        Returns local cell number corresponding to given label.
        If no label corresponds, throws an exception
        
        Returns:
            cell number (int)
        """

    # some basic iterators
    def vertices(self):
        return MeshIterator(self, VERTICES) 

    def cells(self):
        return MeshIterator(self, CELLS)


class UnstructuredMesh(Mesh):
    """
    Represents unstructured mesh. Maintains the list of vertices and cells.
    Attributes:
      vertexList: list of vertices
      cellList: list of interpolation cells   
      vertexOctree: vertex spatial localizer 
      cellOctree: cell spatial localizer
    """

    def __init__(self):
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
        Initialize the receicer according to given vertex and cell lists.
        """
        self.vertexList = vertexList
        self.cellList = cellList

    def copy(self):
        """
        This will return a copy of the receiver. 
        Note:
             DeepCopy will not work, as individual cells contain mesh link attributes, leading to 
             underliing mesh duplication in every cell!
        Returns:
             Copy of receiver (UnstructuredMesh)
        """
        vertexList = []
        cellList   = []
        for i in self.vertices():
            vertexList.append(copy.deepcopy(v))
        for i in self.cells():
            cellList.append(i.copy())
        return UnstructuredMesh(vertexList,cellList)


    def getNumberOfVertices(self):
        """Returns the number of Vertices."""
        return len(self.vertexList)

    def getNumberOfCells(self):
        """Returns the number of Cells."""
        return len(self.cellList)

    def getVertex(self, i):
        return self.vertexList[i]

    def getCell(self, i):
        return self.cellList[i]

    def giveVertexLocalizer(self):
        """Returns the vertex localizer."""
        if self.vertexOctree: 
            return self.vertexOctree
        else:
            # loop over vertices to get bounding box first
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

            #setup vertex localizer
            size = max ( y-x for x,y in zip (minc,maxc))
            mask = [(y-x)>0.0 for x,y in zip (minc,maxc)]
            self.vertexOctree = Octree.Octree(minc, size, mask) 
            if debug: 
                t0=time.clock()
                print "Mesh: setting up vertex octree ...\nminc=", minc,"size:", size, "mask:",mask,"\n",
            # add mesh vertices into octree
            for vertex in self.vertices():
                self.vertexOctree.insert(vertex)
            if debug: print "done in ", time.clock() - t0, "[s]"

            return self.vertexOctree

    def giveCellLocalizer(self):
       """Returns the cell localizer."""
       if self.cellOctree: 
           return self.cellOctree
       else:
           # loop over cell bboxes to get bounding box first
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
                       
       #setup vertex localizer
       size = max ( y-x for x,y in zip (minc,maxc))
       mask = [(y-x)>0.0 for x,y in zip (minc,maxc)]
       self.cellOctree = Octree.Octree(minc, size, mask) 
       if debug: 
           t0=time.clock()
           print "Mesh: setting up vertex octree ...\nminc=", minc,"size:", size, "mask:",mask,"\n",
       for cell in self.cells():
           self.cellOctree.insert(cell)
       if debug: print "done in ", time.clock() - t0, "[s]"
       return self.cellOctree

    def __buildVertexLabelMap(self):
        self.vertexDict = {}
        # loop over vertex lists in both meshes
        for v in xrange(len(self.vertexList)):
            if (self.vertexDict.has_key(self.vertexList[v].label)):
                if debug:
                    print "UnstructuredMesh::buildVertexLabelMap: multiple entry detected, vertex label ",  self.vertexList[v].label
            else:
                self.vertexDict[self.vertexList[v].label]=v
       
    def __buildCellLabelMap(self):
        self.cellDict = {}
        # loop over vertex lists in both meshes
        for v in xrange(len(self.cellList)):
            if (self.cellDict.has_key(self.cellList[v].label)):
                if debug:
                    print "UnstructuredMesh::buildCellLabelMap: multiple entry detected, cell label ",  self.cellList[v].label
            else:
                self.cellDict[self.cellList[v].label]=v


    def vertexLabel2Number(self, label):
        """Returns local vertex number corresponding to given label.
        If no label corresponds, thows an exception"""
        if (not self.vertexDict):
            self.__buildVertexLabelMap()
        return self.vertexDict[label]

        
    def cellLabel2Number(self, label):
        """Returns local cell number corresponding to given label.
        If no label corresponds, thows an exception"""
        if (not self.cellDict):
            self.__buildCellLabelMap()
        return self.cellDict[label]


    def merge (self, mesh):
        """
        Merges receiver with given mesh. This is based on merging mesh entities (vertices, cells) based on their labels,
        as they refer to global ids of each entity, that should be unique
        
        The procedure used here is based on creating a dictionary for every componenet from both meshes, where the key is component label
        so that the entities wth the same id could be easily identified.
        """

        #build vertex2local reciver map first
        if (not self.vertexDict):
            self.__buildVertexLabelMap()
        #
        #merge vertexLists
        #
        if debug: print "UnstructuredMesh::merge: merged vertices with label:",
        for v in mesh.vertices():
            if (self.vertexDict.has_key(v.label)):
                if debug:
                    print v.label,
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
            self.__buildCellLabelMap()

        if debug: print "UnstructuredMesh::merge: merged cells with label:",
        for c in mesh.cells():
            if (self.cellDict.has_key(c.label)):
                if debug:
                    print c.label,
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
        print
        #last step: invalidate receiver 
        self.vertexOctree = None
        self.cellOctree = None



