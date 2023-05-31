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
from __future__ import annotations

from . import apierror
from . import octree
from . import bbox
from . import baredata
from . import vertex
from . import cell
from . import units
from . import util
from . import localizer
from .heavydata import HeavyConvertible
import copy
import time
import sys
import os.path
import numpy
import Pyro5
import dataclasses
import typing
from . import cellgeometrytype
import pickle
import deprecated
import numpy as np

import pydantic

# enum to distinguish iterartors provided by domain
VERTICES = 0
CELLS = 1

# debug flag
debug = 0


@Pyro5.api.expose
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
        :param int type: Type of mesh, e.g. VERTICES or CELLS
        """
        if type == VERTICES or type == CELLS:
            self.type = type
            self.mesh = mesh
        else:
            print("Unsupported iterator type")
            sys.exit(0)

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


@Pyro5.api.expose
class Mesh(baredata.BareData):
    """
    Abstract representation of a computational domain.
    Mesh contains computational cells and vertices.
    Derived classes represent structured, unstructured FE grids, FV grids, etc.

    Mesh is assumed to provide a suitable instance of cell and vertex localizers.

    .. automethod:: __init__
    """

    mapping: typing.Any = None
    unit: typing.Union[str,units.Unit]=None

    def __repr__(self): return str(self)

    def __str__(self):
        return f'<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}, {self.getNumberOfVertices()} vertices, {self.getNumberOfCells()} cells>'

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._setDirty()
        if hasattr(self,'_postDump'): self._postDump()

    def _setDirty(self):
        'Invalidate (reset) cached data'
        self._vertexOctree=None
        self._cellOctree=None

    @classmethod
    def loadFromLocalFile(cls, fileName):
        """
        Alternative constructor which loads an instance from a Pickle module.

        :param str fileName: File name

        :return: Returns Mesh instance
        :rtype: Mesh
        """
        return pickle.load(open(fileName, 'rb'))

    def copy(self):
        """
        Returns a copy of the receiver.

        :return: A copy of the receiver
        :rtype: Copy of the receiver, e.g. Mesh

        .. note:: DeepCopy will not work, as individual cells contain mesh link attributes, leading to underlying mesh duplication in every cell!
        """
    def getNumberOfVertices(self):
        """
        Get number of vertices (nodes).

        :return: Number of Vertices
        :rtype: int
        """
        return 0

    def getNumberOfCells(self):
        """
        Return number of cells (finite elements).

        :return: The number of Cells
        :rtype: int
        """
        return 0

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
        nv = self.getNumberOfVertices()
        ret = numpy.empty((nv, 3), dtype=numpy.float64)
        for i in range(0, nv):
            ret[i] = numpy.array(self.getVertex(i).getCoordinates())
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
        Return all cells as 2x numpy.array; each i-th row contains vertex indices for i-th cell. Does in 2 passes,
        first to determine maximum number of vertices per cell (to shape the field accordingly). For cells with less
        vertices than the maximum, excess ones are assigned the invalid value of -1.

        :return: (cell_types,cell_vertices)
        :rtype: (numpy.array,numpy.array)

        .. note:: This method has not been tested yet.
        """
        # determine the maximum number of vertices
        mnv = 0
        nc = self.getNumberOfCells()
        for i in range(nc):
            mnv = max(mnv, self.getCell(i).getNumberOfVertices())
        tt, cc = numpy.empty(shape=(nc,), dtype=numpy.int64), numpy.full(shape=(nc, mnv), fill_value=-1, dtype=numpy.int64)
        for i in range(nc):
            c = self.getCell(i)
            tt[i] = c.getGeometryType()
            vv = numpy.array([v.getNumber() for v in c.getVertices()], dtype=numpy.int64)
            cc[i, :len(vv)] = vv  # excess elements in the row stay at -1
        return tt, cc

    def toMeshioPointsCells(self):
        import numpy as np
        ret = {}
        for ic in range(self.getNumberOfCells()):
            c = self.getCell(ic)
            t = c.getMeshioGeometryStr()
            ids = [v.getNumber() for v in c.getVertices()]
            if t in ret:
                ret[t].append(ids)
            else:
                ret[t] = [ids]
        return self.getVertices(), [(vert_type, np.array(ids)) for vert_type, ids in ret.items()]

    def toMeshioMesh(self):
        import meshio
        return meshio.Mesh(*self.toMeshioPointsCells())

    @staticmethod
    def makeFromMeshioMesh(mesh):
        return Mesh.makeFromMeshioPointsCells(mesh.points, mesh.cells)

    @staticmethod
    def makeFromMeshioPointsCells(points, cells):
        ret = UnstructuredMesh()
        vv = [vertex.Vertex(number=row, label=None, coords=tuple(points[row])) for row in range(points.shape[0])]
        cc = []
        cgt = cellgeometrytype
        c0 = 0
        from . import cell
        for block in cells:
            klass = cell.Cell.getClassForCellGeometryType(cgt.meshioName2cgt[block.type])
            cc += [klass(mesh=ret, number=c0+row, label=None, vertices=tuple(block.data[row])) for row in range(block.data.shape[0])]
            c0 += block.data.shape[0]
        ret.setup(vertexList=vv, cellList=cc)
        return ret

    def asVtkUnstructuredGrid(self):
        """
        Return an object as a vtk.vtkUnstructuredMesh instance.
        
        :return: vtk
        :rtype: vtk.vtkUnstructuredGrid()
        
        .. note:: This method uses the compiled vtk module (which is a wrapper atop the c++ VTK library) -- in contrast         to :obj:`UnstructuredMesh.getVTKRepresentation`, which uses the pyvtk module (python-only implementation of VTK i/o supporting only VTK File Format version 2).
        """
        import vtk
        # vertices
        pts = vtk.vtkPoints()
        for ip in range(self.getNumberOfVertices()):
            pts.InsertNextPoint(self.getVertex(ip).getCoordinates())
        # cells
        cells, cellTypes = vtk.vtkCellArray(), []
        for ic in range(self.getNumberOfCells()):
            c = self.getCell(ic)
            cgt = c.getGeometryType()
            cellGeomTypeMap = {
                cellgeometrytype.CGT_TRIANGLE_1: (vtk.vtkTriangle, vtk.VTK_TRIANGLE),
                cellgeometrytype.CGT_QUAD:       (vtk.vtkQuad, vtk.VTK_QUAD),
                cellgeometrytype.CGT_TETRA:      (vtk.vtkTetra, vtk.VTK_TETRA),
                cellgeometrytype.CGT_HEXAHEDRON: (vtk.vtkHexahedron, vtk.VTK_HEXAHEDRON),
                cellgeometrytype.CGT_TRIANGLE_2: (vtk.vtkQuadraticTriangle, vtk.VTK_QUADRATIC_TRIANGLE)
            }
            c2klass, c2type = cellGeomTypeMap[cgt]  # instantiate the VTK cell with the correct type
            c2 = c2klass()
            verts = c.getVertices()  # those should be all instances of Vertex...? Hopefully so.
            for i, v in enumerate(verts):
                c2.GetPointIds().SetId(i, v.getNumber())
            cells.InsertNextCell(c2)
            cellTypes.append(c2type)
        ret = vtk.vtkUnstructuredGrid()
        ret.SetPoints(pts)
        ret.SetCells(cellTypes, cells)
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
        for i in range(0, self.getNumberOfVertices()):
            yield self.getVertex(i)

    def cells(self):
        for i in range(0, self.getNumberOfCells()):
            yield self.getCell(i)

    def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
        """
        Dump Mesh to a file using a Pickle serialization module.

        :param str fileName: File name
        :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
        """
        pickle.dump(self, open(fileName, 'wb'), protocol)

    @deprecated.deprecated('use getVertexLocalizer instead')
    def giveVertexLocalizer(self): return self.getVertexLocalizer()

    def getGlobalBBox(self):
        vvv = self.vertices()
        c0 = next(iter(vvv)).getCoordinates()  # use the first bbox as base
        bb = bbox.BBox(c0, c0)  # ope-pointed bbox
        # XXX replace by call to getVertices()
        for vert in vvv:
            bb.merge(vert.getCoordinates())  # extend it with all other cells
        return bb

    def getVertexLocalizer(self):
        """
        :return: Returns the vertex localizer.
        :rtype: Octree
        """
        if self._vertexOctree: 
            return self._vertexOctree
        else:
            bb = self.getGlobalBBox()
            minc, maxc = bb.coords_ll, bb.coords_ur
            # setup vertex localizer
            size = max(y-x for x, y in zip(minc, maxc))
            mask = [(y-x) > 0.0 for x, y in zip(minc, maxc)]
            self._vertexOctree = octree.Octree(minc, size, tuple(mask))
            if debug: 
                t0 = time.clock()
                print("Mesh: setting up vertex octree ...\nminc=", minc, "size:", size, "mask:", mask, "\n")
            # add mesh vertices into octree
            for iv, vertex in enumerate(self.vertices()):
                if debug:
                    print(f'  {iv=}, {vertex=}')
                self._vertexOctree.insert(iv, vertex.getBBox())
            if debug:
                print("done in ", time.clock() - t0, "[s]")

            return self._vertexOctree

    def getCellLocalizer(self):
        """
        Get the cell localizer.

        :return: Returns the cell localizer.
        :rtype: Octree
        """
        if debug:
            t0 = time.time()
        if self._cellOctree: 
            return self._cellOctree
        else:
            if debug:
                print('Start at: ', time.time()-t0)
            if 0:
                ccc = self.cells()
                bb = ccc.__iter__().__next__().getBBox()  # use the first bbox as base
                i=0
                for cell in ccc:
                    bb.merge(cell.getBBox())  # extend it with all other cells
                    if i%1000==0: print(f'{i}')
                    i+=1
            bb=self.getGlobalBBox()
            minc, maxc = bb.coords_ll, bb.coords_ur

            if debug:
                print('Cell bbox: ', time.time()-t0)

        # setup cell localizer
        size = max(y-x for x, y in zip(minc, maxc))
        mask = [(y-x) > 0.0 for x, y in zip(minc, maxc)]
        self._cellOctree = octree.Octree(minc, size, tuple(mask))
        if debug:
            print('Octree ctor: ', time.time()-t0)
            print("Mesh: setting up cell octree ...\nminc=", minc, "size:", size, "mask:", mask, "\n")
        import tqdm
        for ic, cell in enumerate(tqdm.tqdm(self.cells(), unit=' cells', total=self.getNumberOfCells())):
            self._cellOctree.insert(ic, cell.getBBox())
        if debug:
            print("done in ", time.time() - t0, "[s]")
        return self._cellOctree


    def asHdf5Object(self, parentgroup, heavyMesh=None):
        raise NotImplementedError('This method is abstract, derived classes must override.')

    @classmethod
    def isHere(klass,*,h5grp): return False

    @staticmethod
    def makeFromHdf5group(h5grp):
        def _get_subclasses(cls):
            ret=set([cls])
            for sc in cls.__subclasses__():
                ret|=_get_subclasses(sc)
            return ret
        for sub in _get_subclasses(Mesh):
            if sub.isHere(h5grp=h5grp):
                return sub.makeFromHdf5group(h5grp=h5grp)




@Pyro5.api.expose
class UnstructuredMesh(Mesh,HeavyConvertible):
    """
    Represents unstructured mesh. Maintains the list of vertices and cells.

    The class contains:

    * vertexList: list of vertices
    * cellList: list of interpolation cells
    * _vertexOctree: vertex spatial localizer
    * _cellOctree: cell spatial localizer
    * _vertexDict: vertex dictionary
    * _cellDict: cell dictionary

    .. automethod:: __init__
    .. automethod:: __buildVertexLabelMap__
    .. automethod:: __buildCellLabelMap__
    """

    vertexList: typing.List[vertex.Vertex]=pydantic.Field(default_factory=lambda: [])
    cellList: typing.List[cell.Cell]=pydantic.Field(default_factory=lambda: [])

    def __init__(self, **kw):
        super().__init__(**kw)
        self._vertexDict = None
        self._cellDict = None

    def _postDump(self):
        """Called when the instance is being reconstructed."""
        # print('Mesh._postDump…')
        for i in range(self.getNumberOfCells()):
            object.__setattr__(self.getCell(i), 'mesh', self)


    # this is necessary for putting the mesh into set (in localizer)
    def __hash__(self): return id(self)

    def setup(self, vertexList, cellList):
        """
        Initializes the receicer according to given vertex and cell lists.

        :param list vertexList: A tuple of vertices
        :param list cellList: A tuple of cells
        """
        if isinstance(vertexList, list):
            self.vertexList = vertexList
        elif isinstance(vertexList, tuple):  # temporary fix for compatibility
            self.vertexList = list(vertexList)
        else:
            raise TypeError("Incompatible type of given vertexList.")

        if isinstance(cellList, list):
            self.cellList = cellList
        elif isinstance(cellList, tuple):  # temporary fix for compatibility
            self.cellList = list(cellList)
        else:
            raise TypeError("Incompatible type of given cellList.")

    def copy(self):
        """
        See :func:`mesh.copy`
        """
        vertexList = []
        cellList = []
        for i in self.vertices():
            vertexList.append(copy.deepcopy(i))
        for i in self.cells():
            cellList.append(i.copy())
        ans = UnstructuredMesh()
        ans.setup(vertexList, cellList)
        return ans

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

    def __buildVertexLabelMap__(self):
        """
        Create a custom dictionary between vertex's label and Vertex instance.
        """
        self._vertexDict = {}
        # loop over vertex lists in both meshes
        for v in range(len(self.vertexList)):
            if self.vertexList[v].label in self._vertexDict:
                if debug:
                    print("UnstructuredMesh::buildVertexLabelMap: multiple entry detected, vertex label ",
                          self.vertexList[v].label)
            else:
                self._vertexDict[self.vertexList[v].label] = v

    def __buildCellLabelMap__(self):
        """
        Create a custom dictionary between cell's label and Cell instance.
        """
        self._cellDict = {}
        # loop over vertex lists in both meshes
        for v in range(len(self.cellList)):
            if self.cellList[v].label in self._cellDict:
                if debug:
                    print("UnstructuredMesh::buildCellLabelMap: multiple entry detected, cell label ",
                          self.cellList[v].label)
            else:
                self._cellDict[self.cellList[v].label] = v

    def vertexLabel2Number(self, label):
        """
        See :func:`Mesh.vertexLabel2Number`
        """
        if not self._vertexDict:
            self.__buildVertexLabelMap__()
        return self._vertexDict[label]

    def cellLabel2Number(self, label):
        """
        See :func:`Mesh.cellLabel2Number`
        """
        if not self._cellDict:
            self.__buildCellLabelMap__()
        return self._cellDict[label]

    def merge(self, mesh):
        """
        Merges receiver with a given mesh. This is based on merging mesh entities (vertices, cells) based on their
        labels, as they refer to global IDs of each entity, that should be unique.

        The procedure used here is based on creating a dictionary for every componenet from both meshes, where the key
        is component label so that the entities with the same ID could be easily identified.

        :param Mesh mesh: Source mesh for merging
        """
        # build vertex2local reciver map first
        if not self._vertexDict:
            self.__buildVertexLabelMap__()
        #
        # merge vertexLists
        #
        if debug:
            print("UnstructuredMesh::merge: merged vertices with label:")
        for v in mesh.vertices():
            if v.label in self._vertexDict:
                if debug:
                    print(v.label)
            else:
                indx = len(self.vertexList)
                self.vertexList[indx:] = [copy.deepcopy(v)]
                self._vertexDict[v.label] = indx

        # renumber _vertexDict verices 
        n = 0
        # self.vertexList=[dataclasses.replace(v,number=i) for i,v in enumerate(self.vertexList)]
        for v in self.vertexList:
            v.number = n
            n += 1
        #
        # now merge cell lists
        #

        if not self._cellDict:
            self.__buildCellLabelMap__()

        if debug:
            print("UnstructuredMesh::merge: merged cells with label:")
        for c in mesh.cells():
            if c.label in self._cellDict:
                if debug:
                    print(c.label)
            else:
                # update c vertex list according to new numbering
                updatedVertices = []
                for v in c.getVertices():
                    updatedVertices.append(self._vertexDict[v.label])
                if 1:
                    ccopy = c.copy()
                    ccopy.vertices = tuple(updatedVertices)
                    ccopy.mesh = self
                else: ccopy=dataclasses.replace(c,vertices=tuple(updatedVertices),mesh=self)
                indx = len(self.cellList)
                self.cellList[indx:] = [ccopy]
                self._cellDict[ccopy.label] = indx
        print()
        # last step: invalidate receiver
        self._vertexOctree = None
        self._cellOctree = None

    def getVTKRepresentation(self):
        """
        Get VTK representatnion of the mesh.

        return: VTK representation of the receiver. Requires pyvtk module.
        :rtype: pyvtk.UnstructuredGrid
        """
        import pyvtk

        vertices = []
        hexahedrons = []
        tetrahedrons = []
        quads = []
        triangles = []

        # oop over receiver vertices and create list of vertex coordinates
        for v in range(len(self.vertexList)):
            vertices.append(self.vertexList[v].coords)
        # loop over receiver cells
        for c in range(len(self.cellList)):
            cell = self.cellList[c]
            cgt = cell.getGeometryType()
            if cgt == cellgeometrytype.CGT_TRIANGLE_1:
                triangles.append(cell.vertices)
            elif cgt == cellgeometrytype.CGT_QUAD:
                quads.append(cell.vertices)
            elif cgt == cellgeometrytype.CGT_TETRA:
                tetrahedrons.append(cell.vertices)
            elif cgt == cellgeometrytype.CGT_HEXAHEDRON:
                hexahedrons.append(cell.vertices)
            elif cgt == cellgeometrytype.CGT_TRIANGLE_2:
                # no direct support in pyvtk. map it to linear tringles
                triangles.append((cell.vertices[0], cell.vertices[3], cell.vertices[5]))
                triangles.append((cell.vertices[1], cell.vertices[4], cell.vertices[3]))
                triangles.append((cell.vertices[2], cell.vertices[5], cell.vertices[4]))
                triangles.append((cell.vertices[3], cell.vertices[4], cell.vertices[5]))
            else:
                msg = "Unsupported cell geometry type encountered: "+str(cgt)
                raise apierror.APIError(msg)

        return pyvtk.UnstructuredGrid(
            vertices, hexahedron=hexahedrons, tetra=tetrahedrons, quad=quads, triangle=triangles)

    @staticmethod
    def makeFromVtkUnstructuredGrid(ugrid):
        """Create a new instance of :obj:`UnstructuredMesh` based on VTK's unstructured grid object. Cell types are
        mapped between VTK and mupif (supported: vtkTriangle, vtkQuadraticTriangle, vtkQuad, vtkTetra, vtkHexahedron).

        :param ugrid: instance of vtk.vtkUnstructuredGrid
        :return: new instance of :obj:`UnstructuredMesh`
        """
        import vtk
        from . import cell, vertex
        ret = UnstructuredMesh()
        np, nc = ugrid.GetNumberOfPoints(), ugrid.GetNumberOfCells()
        # vertices
        mupifVertices = [vertex.Vertex(number=ip, label=ip, coords=ugrid.GetPoint(ip)) for ip in range(np)]
        # cells
        mupifCells = []
        for ic in range(nc):
            c = ugrid.GetCell(ic)
            pts = [c.GetPointId(i) for i in range(c.GetNumberOfPoints())]
            # map VTK type to our type?
            # or don't care and used cell types array to reconstruct cells
            # assuming that cell types were stored correctly and numbering did not change meanwhile
            # plus add safety check for the required number of points per cell
            cellGeomTypeMap = {
                vtk.VTK_TRIANGLE:           cellgeometrytype.CGT_TRIANGLE_1,
                vtk.VTK_QUADRATIC_TRIANGLE: cellgeometrytype.CGT_TRIANGLE_2,
                vtk.VTK_TETRA:              cellgeometrytype.CGT_TETRA,
                vtk.VTK_QUAD:               cellgeometrytype.CGT_QUAD,
                vtk.VTK_HEXAHEDRON:         cellgeometrytype.CGT_HEXAHEDRON,
            }
            # find mupif class of the cell
            # if the lookup fails, KeyError propagates to the caller, which is what we want
            cgt = cellGeomTypeMap[c.GetCellType()]
            # create new cell and append to mupifCells
            mupifCells.append(
                cell.Cell.getClassForCellGeometryType(cgt)(
                    # mesh=ret, number=ic, label=None, vertices=[mupifVertices[i] for i in pts]
                    mesh=ret, number=ic, label=None, vertices=pts
                )
            )
        ret.setup(vertexList=mupifVertices, cellList=mupifCells)
        return ret

    @staticmethod
    def makeFromPyvtkUnstructuredGrid(ugr):
        """Create a new instance of :obj:`UnstructuredMesh` based on pyvtk.UnstructuredGrid object. Cell types are
        mapped between pyvtk and mupif (supported: triangle, tetra, quad, hexahedron).

        :param ugr: instance of pyvtk.UnstructuredGrid
        :return: new instance of :obj:`UnstructuredMesh`
        """
        from . import cell, vertex
        ret = UnstructuredMesh()
        cells = []
        vertices = [vertex.Vertex(number=ip, label=ip, coords=ugr.points[ip]) for ip in range(len(ugr.points))]
        for cellName in ['vertex', 'poly_vertex', 'line', 'poly_line', 'triangle', 'triangle_strip', 'polygon', 'pixel',
                         'quad', 'tetra', 'voxel', 'hexahedron', 'wedge', 'pyramid']:
            if not hasattr(ugr, cellName):
                continue
            val = getattr(ugr, cellName)
            if val == [] or (len(val) == 1 and val[0] == []):
                continue  # no cells of this type
            # print(cellName,val)
            cellGeomNameMap = {
                'triangle':   cellgeometrytype.CGT_TRIANGLE_1,
                'tetra':      cellgeometrytype.CGT_TETRA,
                'quad':       cellgeometrytype.CGT_QUAD,
                'hexahedron': cellgeometrytype.CGT_HEXAHEDRON,
            }
            try:
                cgt = cellGeomNameMap[cellName]
            except KeyError:
                raise NotImplementedError("pyvtk cell type '%s' is not handled by the mupif import routine." % cellName)
            cells.append([
                cell.Cell.getClassForCellGeometryType(cgt)(
                    mesh=ret,
                    number=len(cells),
                    label=None,
                    vertices=[vertices[i].number for iv in val[i]]
                ) for i in range(len(val))
            ])
        ret.setup(vertexList=vertices, cellList=cells)
        return ret

    def dataDigest(self):
        """Internal function returning hash digest of all internal data, for the purposes of identity test."""
        mvc, (mct, mci) = self.getVertices(), self.getCells()
        return util.sha1digest([mvc,mct,mci])

    def asHdf5Object(self, parentgroup, heavyMesh=False):
        """
        Return the instance as HDF5 object.
        Complementary to :obj:`makeFromHdf5Object` which will restore the instance from that data.
        """
        mhash = self.dataDigest()
        if mhash in parentgroup:
            return parentgroup[mhash]
        gg = parentgroup.create_group(name=mhash)
        if not heavyMesh: self.toHdf5Group(gg)
        else:
            from mupif import HeavyUnstructuredMesh
            # TODO: don't use meshio in-memory mesh as intermediary, convert in chunks directly
            HeavyUnstructuredMesh.fromMeshioMesh_static(h5grp=gg,mesh=self.toMeshioMesh(),progress=True,chunk=10000)
        return gg

    def toHdf5Group(self, group):
        mvc, (mct, mci) = self.getVertices(), self.getCells()
        for name, data in ('vertex_coords', mvc), ('cell_types', mct), ('cell_vertices', mci):
            group[name] = data
        group.attrs['unit']=('' if self.unit is None else str(self.unit))
        group.attrs['__class__'] = self.__class__.__name__
        group.attrs['__module__'] = self.__class__.__module__

    @classmethod
    def isHere(klass,*,h5grp):
        for ds in ['vertex_coords','cell_types','cell_vertices']:
            if ds not in h5grp: return False
        from mupif.heavymesh import HeavyUnstructuredMesh
        if HeavyUnstructuredMesh.GRP_CELL_OFFSETS in h5grp: raise IOError(f'{klass.__name__}: {HeavyUnstructuredMesh.GRP_CELL_OFFSETS} must not be present (is that a HeavyUnstructuredMesh?)')
        return True
    

    @staticmethod
    def makeFromHdf5group(h5grp):
        """
        Create new :obj:`Mesh` instance from given hdf5 object. Complementary to :obj:`asHdf5Object`.

        Constructs HeavyUnstructuredMesh if data are saved in that format.

        :return: new instance
        :rtype: :obj:`Mesh` or its subclass
        """
        # instantiate the right Mesh subclass
        import importlib
        from mupif.vertex import Vertex
        from mupif.cell import Cell
        assert UnstructuredMesh.isHere(h5grp=h5grp)
        klass = getattr(importlib.import_module(h5grp.attrs['__module__']), h5grp.attrs['__class__'])
        ret = klass()
        mvc, mct, mci = h5grp['vertex_coords'], h5grp['cell_types'], h5grp['cell_vertices']
        # construct vertices
        vertices = [Vertex(number=vi, label=None, coords=tuple(mvc[vi])) for vi in range(mvc.shape[0])]
        cells = [
            Cell.getClassForCellGeometryType(mct[ci])(
                mesh=ret,
                number=ci,
                label=None,
                # vertices=tuple(mci[ci])
                vertices=[vertices[i].number for i in mci[ci]]
            ) for ci in range(mct.shape[0])
        ]
        ret.setup(vertexList=vertices, cellList=cells)
        return ret
