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

from . import cell
from . import bbox
from . import apierror
from . import mupifobject
from .dataid import DataID
from . import cellgeometrytype
from . import mesh
from . import mupifquantity
from .units import Quantity, Unit
from .dumpable import NumpyArray

import meshio
import sys

import pydantic
import typing

from numpy import array, arange, random, zeros
import numpy
import numpy as np
import copy
import Pyro5
from enum import IntEnum
import pydantic
import pickle
import logging
import itertools
import os.path
from .units import Unit
log = logging.getLogger()

# debug flag
debug = 0


class FieldType(IntEnum):
    """
    Represent the supported values of FieldType, i.e. FT_vertexBased or FT_cellBased.
    """
    FT_vertexBased = 1
    FT_cellBased = 2


@Pyro5.api.expose
class FieldBase(mupifquantity.MupifQuantity):
    fieldID: DataID
    time: Quantity = 0*Unit('s')

    def __init__(self, **kw):
        super().__init__(**kw)

    def getDataID(self):
        """
        Returns DataID, e.g. FID_Displacement, FID_Temperature.

        :return: Returns field DataID
        :rtype: DataID
        """
        return self.fieldID

    def getFieldID(self):
        """
        Returns DataID, e.g. FID_Displacement, FID_Temperature.

        :return: Returns field DataID
        :rtype: DataID
        """
        return self.fieldID

    def getFieldIDName(self):
        """
        Returns name of the field.

        :return: Returns DataID name
        :rtype: string
        """
        return self.fieldID.name

    def getTime(self):
        """
        Get time of the field.

        :return: Time of field data
        :rtype: units.Quantity
        """
        return self.time

    @pydantic.validate_arguments
    def evaluate(self, positions, eps: float = 0.0):
        """
        Evaluates the receiver at given spatial position(s).

        :param positions: 1D/2D/3D position vectors
        :type positions: tuple, a list of tuples
        :param float eps: Optional tolerance for probing whether the point belongs to a cell (should really not be used)
        :return: field value(s)
        :rtype: units.Quantity with given value or tuple of values
        """
        raise RuntimeError('FieldBase.evaluate is abstract.')


@Pyro5.api.expose
class AnalyticalField(FieldBase):
    expr: str
    dim: pydantic.conint(ge=2, le=3) = 3

    def __init__(self, *, unit, **kw):
        # quantity with null array; only the unit is relevant
        super().__init__(quantity=np.array([])*Unit(unit), **kw)

    @pydantic.validate_arguments
    def evaluate(
            self,
            positions: typing.Union[
                typing.List[typing.Tuple[float, float, float]],  # list of 3d coords
                typing.List[typing.Tuple[float, float]],  # list of 2d coords
                typing.Tuple[float, float, float],  # single 3d coords
                typing.Tuple[float, float],  # single 2d coord
                NumpyArray,
                Quantity
            ],
            eps: float = 0.0):
        if isinstance(positions, Quantity):
            if self.mesh.unit is not None:
                positions = positions.to(self.mesh.unit).value
            else:
                raise RuntimeError(f'position has unit "{positions.unit}", but mesh has no unit defined.')
        import numexpr as ne
        loc = dict(x=positions[..., 0], y=positions[..., 1])
        if self.dim == 2:
            loc['xy'] = positions
        if self.dim == 3:
            loc.update({'z': positions[..., 2], 'xyz': positions})
        return self.quantity.unit*ne.evaluate(self.expr, loc)


@Pyro5.api.expose
class Field(FieldBase):
    """
    Representation of field. Field is a scalar, vector, or tensorial
    quantity defined on a spatial domain. The field, however is assumed
    to be fixed at certain time. The field can be evaluated in any spatial point
    belonging to underlying domain.

    Derived classes will implement fields defined on common discretizations,
    like fields defined on structured/unstructured FE meshes, FD grids, etc.

    .. automethod:: __init__
    .. automethod:: _evaluate
    """
    #: Instance of a Mesh class representing the underlying discretization.
    mesh: mesh.Mesh
    #: whether the field is vertex-based or cell-based
    fieldType: FieldType = FieldType.FT_vertexBased

    def __repr__(self): return str(self)

    def __str__(self):
        return f'<{self.__class__.__module__}.{self.__class__.__name__} at {hex(id(self))}, {self.getFieldIDName()}, time={self.getTime()}, unit={str(self.quantity.unit)}, dim={"×".join([str(s) for s in self.quantity.shape]) if self.quantity.ndim>0 else "scalar"}, mesh={str(self.mesh)} >'

    def __init__(self, **kw):
        super().__init__(**kw)  # this calls the real ctor
        # fix zero values
        if 1:
            if len(self.quantity) == 0:
                if self.fieldType == FieldType.FT_vertexBased:
                    ncomp = self.mesh.getNumberOfVertices()
                else:
                    ncomp = self.mesh.getNumberOfCells()
                self.quantity = Quantity(value=np.zeros((ncomp, self.valueType.getNumberOfComponents())), unit=self.quantity.unit)
        # add some extra metadata
        self.updateMetadata({
            'Units': self.getUnit().to_string(),
            'Type': 'mupif.field.Field',
            'Type_ID': str(self.fieldID),
            'FieldType': str(self.fieldType),
            'ValueType': str(self.valueType)
        })

    def getUnit(self) -> Unit:
        """
        Returns representation of property units.
        """
        return self.quantity.unit

    def setRecord(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :param tuple value: Value to be set for a given component, should have the same units as receiver
        """
        self.quantity.value[componentID] = value

    def getRecord(self, componentID):
        """Return value in one point (cell, vertex or similar)"""
        return self.quantity.value[componentID]

    def getRecordQuantity(self, componentID):
        """Return value in one point (cell, vertex or similar)"""
        return self.quantity[componentID]

    def getRecordSize(self):
        """
        Return the number of scalars per value, depending on :obj:`valueType` passed when constructing the instance.

        :return: number of scalars (1,3,9 respectively for scalar, vector, tensor)
        :rtype: int
        """
        return self.valueType.getNumberOfComponents()

    def getMesh(self):
        """
        Obtain mesh.

        :return: Returns a mesh of underlying discretization
        :rtype: mesh.Mesh
        """
        return self.mesh

    def getFieldID(self):
        """
        Returns DataID, e.g. FID_Displacement, FID_Temperature.

        :return: Returns field ID
        :rtype: DataID
        """
        return self.fieldID

    def getFieldIDName(self):
        """
        Returns name of the field.

        :return: Returns fieldID name
        :rtype: string
        """
        return self.fieldID.name

    def getFieldType(self):
        """
        Returns receiver field type (values specified as vertex or cell values)

        :return: Returns fieldType id
        :rtype: FieldType
        """
        return self.fieldType

    def getTime(self):
        """
        Get time of the field.

        :return: Time of field data
        :rtype: units.Quantity
        """
        return self.time

    @pydantic.validate_arguments
    def evaluate(
            self,
            positions: typing.Union[
                typing.List[typing.Tuple[float, float, float]],  # list of 3d coords
                typing.List[typing.Tuple[float, float]],  # list of 2d coords
                typing.Tuple[float, float, float],  # single 3d coords
                typing.Tuple[float, float],  # single 2d coord
                NumpyArray,
                Quantity,
            ],
            eps: float = 0.0):
        """
        Evaluates the receiver at given spatial position(s).

        :param positions: 1D/2D/3D position vectors
        :type positions: tuple, a list of tuples
        :param float eps: Optional tolerance for probing whether the point belongs to a cell (should really not be used)
        :return: field value(s)
        :rtype: units.Quantity with given value or tuple of values
        """
        # test if positions is a list of positions
        if isinstance(positions, list):
            ans = []
            for pos in positions:
                ans.append(self._evaluate(pos, eps))
            return Quantity(value=ans, unit=self.getUnit())
        else:
            # single position passed
            return Quantity(value=self._evaluate(positions, eps), unit=self.getUnit())

    def _evaluate(self, position, eps):
        """
        Evaluates the receiver at a single spatial position.

        :param tuple position: 1D/2D/3D position vector
        :param float eps: Optional tolerance
        :return: field value
        :rtype: tuple  of doubles 

        .. note:: This method has some issues related to https://sourceforge.net/p/mupif/tickets/22/ .
        """
        if isinstance(position, Quantity):
            if self.mesh.unit is None:
                raise RuntimeError(f'position has unit "{position.unit}" but mesh has no unit defined.')
            position = position.to(self.mesh.unit).value

        cells = self.mesh.getCellLocalizer().getItemsInBBox(bbox.BBox([c-eps for c in position], [c+eps for c in position]))
        # answer=None
        if len(cells):
            # localizer in the newer version returns cell id, not the cell object, check that here
            if isinstance(next(iter(cells)), int):
                cells = [self.mesh.getCell(ic) for ic in cells]

            if self.fieldType == FieldType.FT_vertexBased:
                for icell in cells:
                    try:
                        if icell.containsPoint(position):
                            if debug:
                                log.debug(icell.getVertices())
                            try:
                                answer = icell.interpolate(position, [self.value[i.number] for i in icell.getVertices()])
                            except IndexError:
                                raise RuntimeError('Field::evaluate failed, inconsistent data at cell %d' % icell.label)
                                # raise
                            return answer

                    except ZeroDivisionError:
                        log.error('ZeroDivisionError in Field.evaluate?')
                        log.debug(icell.number)
                        log.debug(position)
                        icell.debug = 1
                        log.debug(icell.containsPoint(position), icell.glob2loc(position))

                # log.error('Field::evaluate - no source cell found for position %s' % str(position))
                for icell in cells:
                    log.debug(icell.number)
                    log.debug(icell.containsPoint(position))
                    log.debug(icell.glob2loc(position))
                raise ValueError(f'Field.evaluate: no source cell found for position {position}')

            else:
                # in case of cell based fields do compute average of cell values containing point
                # this typically happens when point is on the shared edge or vertex
                answer = []
                for icell in cells:
                    if icell.containsPoint(position):
                        if debug:
                            log.debug(icell.getVertices())
                        try:
                            answer.append(self.value[icell.number])
                        except IndexError:
                            log.error('Field::evaluate failed, inconsistent data at cell %d' % icell.label)
                            log.error(icell.getVertices())
                            raise
                if not answer: 
                    raise ValueError(f'Field::evaluate - no source cell found for {position=}')
                else:
                    return np.mean(answer, axis=0)
        else:
            # no source cell found
            # log.error('Field::evaluate - no source cell found for position ' + str(position))
            raise ValueError(f'No source cell found for {position=}')  # + str(position))

    def getVertexValue(self, vertexID):
        """
        Returns the value associated with a given vertex.

        :param int vertexID: Vertex identifier
        :return: The value
        :rtype: units.Quantity
        """
        if self.fieldType == FieldType.FT_vertexBased:
            return Quantity(value=self.getRecord(vertexID), unit=self.getUnit())
        else:
            raise TypeError('Attempt to acces vertex value of cell based field, use evaluate instead')
        
    def getCellValue(self, cellID):
        """
        Returns the value associated with a given cell.

        :param int cellID: Cell identifier
        :return: The value
        :rtype: units.Quantity
        """
        if self.fieldType == FieldType.FT_cellBased:
            return Quantity(value=self.getRecord(cellID), unit=self.getUnit())
        else:
            raise TypeError('Attempt to acces cell value of vertex based field, use evaluate instead')

    def merge(self, field):
        """
        Merges the receiver with given field together. Both fields should be on different parts of the domain (can also overlap), but should refer to same underlying discretization, otherwise unpredictable results can occur.

        :param Field field: given field to merge with.
        """
        # first merge meshes
        mesh = copy.deepcopy(self.mesh)
        mesh.merge(field.mesh)
        log.debug(mesh)
        # merge the field values
        # some type checking first
        if self.fieldType != field.fieldType:
            raise TypeError("Field::merge: fieldType of receiver and parameter is different")
        if self.unit != field.unit:
            raise ValueError('fields have different units (merge is currently not unit-aware; this limitation will be remove with astropy.units)')
        if self.fieldType == FieldType.FT_vertexBased:
            vv = np.zeros_like(self.value, shape=(mesh.getNumberOfVertices(), self.getRecordSize()))
            for f in self, field:
                for v in range(f.mesh.getNumberOfVertices()):
                    vv[mesh.vertexLabel2Number(f.mesh.getVertex(v).label)] = f.getRecord(v)
        else:
            vv = np.zeros_like(self.value, shape=(mesh.getNumberOfCells(), self.getRecordSize()))
            for f in self, field:
                for v in range(f.mesh.getNumberOfCells()):
                    vv[mesh.cellLabel2Number(f.mesh.getCell(v).label)] = f.getRecord(v)

        self.mesh = mesh
        self.value = vv

    def getMartixForTensor(self, values):
        """
        Reshape values to a list with 3x3 arrays. Usable for VTK export.

        :param list values: List containing tuples of 9 values, e.g. [(1,2,3,4,5,6,7,8,9), (1,2,3,4,5,6,7,8,9), ...]
        
        :return: List containing 3x3 matrices for each tensor
        :rtype: list
        """ 
        tensor = []
        for i in values:
            tensor.append(numpy.reshape(i, (3, 3)))
        return tensor

    def plot2D(self, plane="xy", title=None, fieldComponent=0, warpField=None, warpScale=0., fileName=None, show=False, colorbar='horizontal'):
        """ 
        Plots and/or saves 2D image using a matplotlib library. Works for structured and unstructured 2D/3D fields. 2D/3D fields need to define plane. This method gives only basic viewing options, for aesthetic and more elaborated output use e.g. VTK field export with 
        postprocessors such as ParaView or Mayavi. Idea from https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#id1

        :param str plane: what plane to extract from field, valid values are 'xy', 'xz', 'yz'
        :param int fieldComponent: component of the field
        :param str colorbar: color bar details. Valid values '' for no colorbar, 'vertical' or 'horizontal'
        :param str title: title
        :param str fileName: if nonempty, a filename is written to the disk, usually png, pdf, ps, eps and svg are supported
        :param bool show: if the plot should be showed
        :param Field warpField: vector field to wrap geometry
        :param float warpScale: warping scale
        :return: handle to matplotlib figure
        """
        import matplotlib
        import matplotlib.pyplot as plt
        if 0:
            try:
                matplotlib.use('TkAgg')  # Qt4Agg gives an empty, black window
            except ImportError as e:
                log.error('Skipping field2Image2D due to missing modules: %s' % e)
                return None
                # raise
        
        if self.fieldType != FieldType.FT_vertexBased:
            raise apierror.APIError('Only FieldType.FT_vertexBased is now supported')
        
        mesh = self.getMesh()
        numVertices = mesh.getNumberOfVertices()

        indX = 0
        indY = 0
        elev = 0
        if plane == 'xy':
            indX = 0
            indY = 1
            elev = 2
        elif plane == 'xz':
            indX = 0
            indY = 2
            elev = 1
        elif plane == 'yz':
            indX = 1
            indY = 2
            elev = 0
        
        # find eligible vertex points and values
        vx = []
        vy = []
        vertexValue = []
        for i in range(0, numVertices):
            coords = mesh.getVertex(i).getCoordinates()
            if warpField:
                # coords+=warpField.evaluate(coords).getValue()*warpScale
                warpVec = (warpScale * s for s in warpField.evaluate(coords).getValue())
                coords = tuple(map(lambda x, y: x + y, coords, warpVec))
            # print(coords)
            value = self.getRecord(i)[fieldComponent]
            vx.append(coords[indX])
            vy.append(coords[indY])
            vertexValue.append(value)

        if len(vx) == 0:
            log.info('No valid vertex points found, putting zeros on domain 1 x 1')
            for i in range(5):
                vx.append(i % 2)
                vy.append(i/4.)
                vertexValue.append(0)

        # for i in range (0, len(vertexPoints)):
        #     print (vertexPoints[i], vertexValue[i])

        # v = np.array(vertexPoints)
        # vertexValueArr = np.array(vertexValue)
        
        xMin = min(vx)
        xMax = max(vx)
        yMin = min(vy)
        yMax = max(vy)
        
        # print(xMin, xMax, yMin, yMax)
        
        # Create the Triangulation; no triangles so Delaunay triangulation created.
        triang = matplotlib.tri.Triangulation(vx, vy)
        mask = matplotlib.tri.TriAnalyzer(triang).get_flat_tri_mask()
        triang.set_mask(mask)
        # pcolor plot.
        plt.figure()
        plt.gca().set_aspect('equal')
        plt.tricontourf(triang, vertexValue)
        if colorbar:
            plt.colorbar(orientation=colorbar)
        plt.tricontour(triang, vertexValue, colors='k')
        plt.scatter(vx, vy, marker='o', c='k', s=1, zorder=10)
        if title:
            plt.title(title)    
        if fileName:
            plt.savefig(fileName, bbox_inches='tight')
        # if show:
        #     matPlotFig.canvas.draw()
        # return plt

    def field2Image2DBlock(self):
        """
        Block an open window from matPlotLib. Waits until closed.
        """
        import matplotlib.pyplot as plt
        plt.ioff()
        plt.show(block=True)

    def dataDigest(self):
        return mupifquantity.MupifQuantity.dataDigest(self, np.array([self.time.value]), np.frombuffer(bytes(self.time.unit), dtype=np.uint8))

    def toHdf5_split_files(self, fieldPrefix: str, meshPrefix: str, flat=True, heavy=False):
        import h5py
        import shutil
        fDigest = self.dataDigest()
        mDigest = self.getMesh().dataDigest()
        for p in (fieldPrefix, meshPrefix):
            os.makedirs(os.path.dirname(p), exist_ok=True)
        fOut, mOut = fieldPrefix+fDigest, meshPrefix+mDigest
        fg5, mg5 = None, None
        if not os.path.exists(fOut):
            fg5 = h5py.File(fOut, 'w', libver='latest')
            if not flat:
                fg5 = fg5.create_group(f'fields/{fDigest}')
        if not os.path.exists(mOut):
            if not heavy:
                mg5 = h5py.File(mOut, 'w', libver='latest')
                if not flat:
                    mg5.create_group(f'meshes/{mDigest}')
            else:
                mOutTmp = mOut+'~heavy~'
                from . import heavymesh
                with heavymesh.HeavyUnstructuredMesh(h5path=mOutTmp, mode='overwrite') as hMesh:
                    hMesh.fromMeshioMesh(self.getMesh().toMeshioMesh())
                    mDigest = hMesh.dataDigest()
                mOut = meshPrefix+mDigest
                shutil.move(mOutTmp, mOut)
        self._to_hdf5_groups(fg5, mg5, heavy=heavy)
        return {'field': fDigest, 'mesh': mDigest}

    def _to_hdf5_groups(self, fg, mg, heavy, meshLink=None):
        if mg is not None:
            self.getMesh().toHdf5Group(mg)
        if fg is not None:
            self.toHdf5Group(fg, meshLink=None)

    def toHdf5(self, fileName: str = None, groupName='component1/part1', h5group=None):
        r"""
        Dump field to HDF5, in a simple format suitable for interoperability (TODO: document).

        :param str fileName: HDF5 file
        :param str groupName:
        :param str h5group: HDF5 group the data will be saved under.

        The HDF hierarchy is like this::

            group
              |
              +--- meshes
              |   +----25aa0aa04457
              |   |   +--- [vertex_coords]
              |   |   +--- [cell_types]
              |   |   \--- [cell_vertices]
              |   +--- 17809e2b86ea
              |      +--- [vertex_coords]
              |      +--- [cell_types]
              |      \--- [cell_vertices]
              +--- fields
                 +--- 1
                 |   +--- -> meshes/25aa0aa04457
                 |   \--- [vertex_values]
                 +--- 2
                 |   +--- -> meshes/17809e2b86ea
                 |   \--- [vertex_values]
                 +--- 3
                     +--- -> meshes/17809e2b86ea
                     \--- [cell_values]


        where ``plain`` names are HDF (sub)groups, ``[bracketed]`` names are datasets, ``{name=value}`` are HDF attributes, ``->`` prefix indicated HDF5 hardlink (transparent to the user); numerical suffixes (``_01``, ...) are auto-allocated. Mesh objects are hardlinked using HDF5 hardlinks if an identical mesh is already stored in the group, based on hexdigest of its full data.

        .. note:: This method has not been tested yet. The format is subject to future changes.
        """
        import h5py
        if fileName is not None:
            if h5group is not None:
                raise ValueError('Only one of *fileName* and *h5group* may be given (not both).')
            hdf = h5py.File(fileName, 'a', libver='latest')
            if groupName not in hdf:
                gg = hdf.create_group(groupName)
            else:
                gg = hdf[groupName]
        elif h5group is not None:
            gg = h5group
        else:
            raise ValueError('One of *fileName* or *h5group* must be given.')
        # raise IOError('Path "%s" is already used in "%s".'%(path,fileName))

        def _lowest(grp, dir, start=1):
            for i in itertools.count(start=start):
                if f'{dir}/{i}' not in grp:
                    return i
        # save mesh (not saved if there already)
        # groupIndex=_lowest(gg,'meshes')
        # newgrp=f'meshes/{_lowest(gg,"meshes")}'
        if 'meshes' not in gg:
            gg.create_group('meshes')
        mh5 = self.getMesh().asHdf5Object(parentgroup=gg['meshes'])

        if len(self.value) > 0:
            fieldIndex = _lowest(gg, 'fields')
            fieldGrp = gg.create_group(f'fields/{fieldIndex}')
            self.toHdf5Group(fieldGrp, meshLink=h5py.SoftLink(mh5.name))
        if fileName is not None:
            hdf.close()  # necessary for windows
        return fieldIndex

    def toHdf5Group(self, fieldGrp, meshLink=None):
        if meshLink is not None:
            fieldGrp['mesh'] = meshLink
        fieldGrp.attrs['fieldID'] = self.fieldID
        fieldGrp.attrs['valueType'] = self.valueType
        # string/bytes may not contain NULL when stored as string in HDF5
        # see http://docs.h5py.org/en/2.3/strings.html
        # that's why we cast to opaque type "void" and uncast using tostring before unpickling
        fieldGrp.attrs['unit'] = numpy.void(pickle.dumps(self.getUnit(), protocol=0))
        fieldGrp.attrs['time'] = numpy.void(pickle.dumps(self.time, protocol=0))
        if self.fieldType == FieldType.FT_vertexBased:
            val = numpy.empty(shape=(self.getMesh().getNumberOfVertices(), self.getRecordSize()), dtype=numpy.float64)
            for vert in range(self.getMesh().getNumberOfVertices()):
                val[vert] = self.getVertexValue(vert).getValue()
            subGrp = 'vertex_values'
            fieldGrp[subGrp] = val
        elif self.fieldType == FieldType.FT_cellBased:
            # raise NotImplementedError("Saving cell-based fields to HDF5 is not yet implemented.")
            val = numpy.empty(shape=(self.getMesh().getNumberOfCells(), self.getRecordSize()), dtype=numpy.float64)
            for cell in range(self.getMesh().getNumberOfCells()):
                val[cell] = self.getCellValue(cell)
            subGrp = 'vertex_values'
            fieldGrp[subGrp] = val
        else:
            raise RuntimeError("Unknown fieldType %d." % self.fieldType)
        # for compatibility with Hdf5RefQuantity
        fieldGrp[subGrp].attrs['unit'] = str(self.getUnit())

    @staticmethod
    def makeFromHdf5_groups(*, fieldGrp, meshGrp=None, meshCache=None, heavy=False):
        import h5py
        f=fieldGrp
        if 'vertex_values' in f:
            fieldType, valDs = FieldType.FT_vertexBased, f['vertex_values']
        elif 'cell_values' in f:
            fieldType, valDs = FieldType.FT_cellBased, f['cell_values']
        else:
            raise ValueError("HDF5/mupif format error: unable to determine field type.")
        fieldID, valueType, unit, time = DataID(f.attrs['fieldID']), f.attrs['valueType'], f.attrs['unit'].tobytes(), f.attrs['time'].tobytes()
        if unit == '':
            unit = None  # special case, handled at saving time
        else: unit = pickle.loads(unit)
        if time == '':
            time = None  # special case, handled at saving time
        else:
            time = pickle.loads(time)
        if meshGrp is not None:
            # creates HeavyUnstructuredMesh if that is the meshGrp storage format
            m = mesh.Mesh.makeFromHdf5Object(meshGrp)
        else:
            if 'mesh' not in f:
                raise ValueError('HDF5/mesh: missing attribute')
            link = f.get('mesh', getlink=True)
            assert isinstance(link, h5py.SoftLink)
            mPath = link.path
            if mPath not in meshCache:
                meshCache[mPath] = mesh.Mesh.makeFromHdf5Object(f['mesh'])
            m = meshCache[mPath]
        if not heavy:
            quantity = Quantity(value=np.array(valDs).tolist(), unit=unit)
        else:
            from .heavydata import Hdf5RefQuantity, Hdf5OwningRefQuantity
            # hack
            if fieldGrp.name == '/':
                quantity = Hdf5OwningRefQuantity(
                    h5path=valDs.file.filename,
                    h5loc=valDs.name,
                    mode='readonly'
                )
                quantity.openData()
            else:
                quantity = Hdf5RefQuantity(dataset=valDs)
        return Field(mesh=m, fieldID=fieldID, quantity=quantity, time=time, valueType=valueType, fieldType=fieldType)

    @staticmethod
    def makeFromHdf5(*, fileName: str = None, group: str = 'component1/part1', h5group=None, indices: typing.Optional[typing.List[int]] = None):
        """
        Restore Fields from HDF5 file.

        :param str fileName: HDF5 file
        :param str group: HDF5 group the data will be read from (IOError is raised if the group does not exist).
        :return: list of new :obj:`Field` instances
        :param h5group:
        :param indices:
        :rtype: [Field,Field,...]

        .. note:: This method has not been tested yet.
        """
        import h5py
        if fileName is not None:
            if h5group is not None:
                raise ValueError('Only one of *fileName* and *h5group* may be given (not both).')
            hdf = h5py.File(fileName, 'r', libver='latest')
            grp = hdf[group]
        elif h5group is not None:
            grp = h5group
        else:
            raise ValueError('One of *fileName*, *h5group* must be given.')
        # load mesh and field data from HDF5
        # if indices is None:
        if indices is None:
            fieldObjs = [obj for obj in grp['fields'].values()]
        else:
            fieldObjs = [grp[f'fields/{ix}'] for ix in indices]
        # construct all meshes as mupif objects
        meshes = {}  # maps HDF5 paths to meshes
        # construct all fields as mupif objects
        ret = []
        for f in fieldObjs:
            ret.append(Field.makeFromHdf5_groups(fieldGrp=f, meshGrp=None, meshCache=meshes))
        if fileName is not None:
            hdf.close()  # necessary for windows
        return ret

    def toMeshioMesh(self):
        return Field.manyToMeshioMesh([self])

    @staticmethod
    # @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def manyToMeshioMesh(
        fields: typing.Sequence[Field]
    ) -> typing.List[Field]:
        import meshio
        if len(fields) == 0:
            raise ValueError('fields must not be enpty.')
        if len(set([f.getMesh() for f in fields])) != 1:
            raise RuntimeError('All fields must share the same mupif.Mesh.')
        msh = fields[0].getMesh()
        points = msh.getVertices()
        cell_data, point_data = {}, {}
        # defined here: https://github.com/nschloe/meshio/blob/6a1b8c4c3db24ea788a8cac00e46c7f9d562e4d0/meshio/_common.py#L189
        points, cells_list = msh.toMeshioPointsCells()
        for f in fields:
            assert f.getFieldType() in (FieldType.FT_vertexBased, FieldType.FT_cellBased)
            ptData = (f.getFieldType() == FieldType.FT_vertexBased)
            rows = (msh.getNumberOfVertices() if ptData else msh.getNumberOfCells())
            cols = f.getRecordSize()
            # sys.stderr.write(f'each record has {cols} components\n')
            # dta=np.ndarray((rows,cols),dtype='float32')
            dta = np.array([f.getRecord(row) for row in range(rows)])
            (point_data if ptData else cell_data)[f.getFieldIDName()] = (dta if ptData else dta.T)
            # print(f.getFieldIDName())
            # print('Is point data?',ptData)
            # print(f.getFieldIDName(),dta.shape)
        return meshio.Mesh(points, cells_list, point_data, cell_data)

    @staticmethod
    def makeFromMeshioMesh(
        input: typing.Union[str, meshio.Mesh],  # could also be buffer, is that useful?
        unit: dict[str, Unit],  # maps field name to Unit
        time: Quantity = Quantity(value=0, unit='s')
    ) -> typing.List[Field]:
        if isinstance(input, str):
            input = meshio.read(input)
        msh = mesh.Mesh.makeFromMeshioPointsCells(input.points, input.cells)
        ret = []
        for data, fieldType in (input.point_data, FieldType.FT_vertexBased), (input.cell_data, FieldType.FT_cellBased):
            for fname, values in data.items():
                # reshape scalar array saved as 1D
                if len(values.shape) == 1:
                    values = np.reshape(values, (-1, 1))
                data_id = None
                try:
                    data_id = DataID[fname]
                except:
                    pass
                if data_id is None:
                    try:
                        data_id = DataID['FID_'+fname]
                    except:
                        pass

                ret.append(Field(
                    mesh=msh,
                    fieldID=data_id,
                    unit=unit.get(fname, None),
                    time=time,
                    valueType=mupifquantity.ValueType.fromNumberOfComponents(values.shape[1]),
                    value=values.tolist(),
                    fieldType=fieldType
                ))
        return ret

    @staticmethod
    def fromMeshioMesh(m): raise NotImplementedError('maybe later')

    def _sum(self, other, sign1, sign2):
        """
        Should return a new instance. As deep copy is expensive,
        this operation should be avoided. Better to modify the field values.
        """
        raise TypeError('Not supported')
 
    def inUnitsOf(self, *units):
        """
        Should return a new instance. As deep copy is expensive,
        this operation should be avoided. Better to use convertToUnits method
        performing in place conversion.
        """
        raise TypeError('Not supported')
