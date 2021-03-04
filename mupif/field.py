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
from .valuetype import ValueType
from . import bbox
from . import apierror
from . import mupifobject
from .dataid import FieldID
from . import cellgeometrytype
#import mupif.mesh
from . import mesh
from .physics import physicalquantities 
from .physics.physicalquantities import PhysicalQuantity, PhysicalUnit

import meshio

import pydantic
import typing

from numpy import array, arange, random, zeros
import numpy
import numpy as np
import copy
import Pyro5
from enum import IntEnum
import logging
log = logging.getLogger()
import pydantic

import pickle

# debug flag
debug = 0


class FieldType(IntEnum):
    """
    Represent the supported values of FieldType, i.e. FT_vertexBased or FT_cellBased.
    """
    FT_vertexBased = 1
    FT_cellBased = 2

@Pyro5.api.expose
class Field(mupifobject.MupifObject): #, PhysicalQuantity):
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

    mesh: mesh.Mesh # 'mupif.mesh.Mesh'
    fieldID: FieldID
    valueType: ValueType
    unit: PhysicalUnit
    time: PhysicalQuantity
    fieldType: FieldType=FieldType.FT_vertexBased
    value: typing.List=[]
    objectID: int=0
    metadata: dict=pydantic.Field(default_factory=dict)

    @pydantic.validator('unit',pre=True,always=True)
    def conv_unit(cls,u):
        if isinstance(u,PhysicalUnit): return u
        return PhysicalUnit(u)

    @pydantic.validator('value',pre=True,always=True)
    def conv_value(cls,v,values,**kwargs):
        if isinstance(v,np.ndarray): return v.tolist()
        if v is None: return []
        return v

    def __init__(self,**kw):
        super().__init__(**kw) # this calls the real ctor
        # fix zero values
        if len(self.value)==0:
            if self.fieldType==FieldType.FT_vertexBased: ncomp=self.mesh.getNumberOfVertices()
            else: ncomp=self.mesh.getNumberOfCells()
            self.value=np.zeros((ncomp,self.valueType.getNumberOfComponents())).tolist()
        # add some extra metadata
        self.updateMetadata({
            'Units':self.unit.name(),
            'Type':'mupif.field.Field',
            'Type_ID':str(self.fieldID),
            'FieldType':str(self.fieldType),
            'ValueType':str(self.valueType)
        })


    #
    # NO LONGER USED
    #
    @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __old_init__(
        self,
        mesh: typing.Any, # should be mupif.mesh.Mesh, but pydantic does not validate subclasses (?)
        fieldID: FieldID,
        valueType: ValueType,
        units: typing.Union[PhysicalUnit,str],
        time: PhysicalQuantity,
        values: typing.Union[typing.List,numpy.ndarray]=None,
        fieldType: FieldType=FieldType.FT_vertexBased,
        objectID: int=0,
        metadata: dict={}):
        """
        Initializes the field instance.

        :param mesh.Mesh mesh: Instance of a Mesh class representing the underlying discretization
        :param FieldID fieldID: Field type (displacement, strain, temperature ...)
        :param ValueType valueType: Type of field values (scalar, vector, tensor). Tensor is a tuple of 9 values. It is changed to 3x3 for VTK output automatically.
        :param Physics.PhysicalUnits units: Field value units
        :param Physics.PhysicalQuantity time: Time associated with field values
        :param values: Field values (format dependent on a particular field type, however each individual value should be stored as tuple, even scalar value)
        :type values: list of tuples representing individual values
        :param FieldType fieldType: Optional, determines field type (values specified as vertex or cell values), default is FT_vertexBased
        :param int objectID: Optional ID of problem object/subdomain to which field is related, default = 0
        :param dict metadata: Optionally pass metadata for merging
        """
        
        super(Field, self).__init__()
        self.mesh = mesh
        self.fieldID = fieldID
        self.valueType = valueType
        self.time = time
        self.uri = None  # pyro uri; used in distributed setting
        # self.log = logging.getLogger()
        self.fieldType = fieldType
        self.objectID = objectID        
        if values is None:
            if self.fieldType == FieldType.FT_vertexBased:
                ncomponents = mesh.getNumberOfVertices()
            else:
                ncomponents = mesh.getNumberOfCells()
            self.value = zeros((ncomponents, self.getRecordSize()))
        else:
            self.value = values

        if physicalquantities.isPhysicalUnit(units):
            self.unit = units
        else:
            self.unit = physicalquantities.findUnit(units)
            

    def getRecordSize(self):
        """
        Return the number of scalars per value, depending on :obj:`valueType` passed when constructing the instance.

        :return: number of scalars (1,3,9 respectively for scalar, vector, tensor)
        :rtype: int
        """
        if self.valueType == ValueType.Scalar:
            return 1
        elif self.valueType == ValueType.Vector:
            return 3
        elif self.valueType == ValueType.Tensor:
            return 9
        else:
            raise ValueError("Invalid value of Field.valueType (%d)." % self.valueType)

    def getMesh(self):
        """
        Obtain mesh.

        :return: Returns a mesh of underlying discretization
        :rtype: mesh.Mesh
        """
        return self.mesh

    def getValueType(self):
        """
        Returns ValueType of the field, e.g. scalar, vector, tensor.

        :return: Returns value type of the receiver
        :rtype: ValueType
        """
        return self.valueType

    def getFieldID(self):
        """
        Returns FieldID, e.g. FID_Displacement, FID_Temperature.

        :return: Returns field ID
        :rtype: FieldID
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
        :rtype: Physics.PhysicalQuantity
        """
        return self.time

    @pydantic.validate_arguments
    def evaluate(self,
        positions: typing.Union[
            typing.List[typing.Tuple[float,float,float]], # list of 3d coords
            typing.List[typing.Tuple[float,float]], # list of 2d coords
            typing.Tuple[float,float,float], # single 3d coords
            typing.Tuple[float,float] # single 2d coord
        ],
        eps: float=0.0):
        """
        Evaluates the receiver at given spatial position(s).

        :param positions: 1D/2D/3D position vectors
        :type positions: tuple, a list of tuples
        :param float eps: Optional tolerance for probing whether the point belongs to a cell (should really not be used)
        :return: field value(s)
        :rtype: Physics.PhysicalQuantity with given value or tuple of values
        """
        # test if positions is a list of positions
        if isinstance(positions, list):
            ans = []
            for pos in positions:
                ans.append(self._evaluate(pos, eps))
            return PhysicalQuantity(value=ans, unit=self.unit)
        else:
            # single position passed
            return PhysicalQuantity(value=self._evaluate(positions, eps), unit=self.unit)

    def _evaluate(self, position, eps):
        """
        Evaluates the receiver at a single spatial position.

        :param tuple position: 1D/2D/3D position vector
        :param float eps: Optional tolerance
        :return: field value
        :rtype: tuple  of doubles 

        .. note:: This method has some issues related to https://sourceforge.net/p/mupif/tickets/22/ .
        """
        cells = self.mesh.giveCellLocalizer().giveItemsInBBox(bbox.BBox([c-eps for c in position], [c+eps for c in position]))
        # answer=None
        if len(cells):
            if self.fieldType == FieldType.FT_vertexBased:
                for icell in cells:
                    try:
                        if icell.containsPoint(position):
                            if debug:
                                log.debug(icell.getVertices())
                            try:
                                answer = icell.interpolate(position, [self.value[i.number] for i in icell.getVertices()])
                            except IndexError:
                                log.error('Field::evaluate failed, inconsistent data at cell %d' % icell.label)
                                raise
                            return answer

                    except ZeroDivisionError:
                        print('ZeroDivisionError?')
                        log.debug(icell.number)
                        log.debug(position)
                        icell.debug = 1
                        log.debug(icell.containsPoint(position), icell.glob2loc(position))

                log.error('Field::evaluate - no source cell found for position %s' % str(position))
                for icell in cells:
                    log.debug(icell.number)
                    log.debug(icell.containsPoint(position))
                    log.debug(icell.glob2loc(position))

            else:  # if (self.fieldType == FieldType.FT_vertexBased):
                # in case of cell based fields do compute average of cell values containing point
                # this typically happens when point is on the shared edge or vertex
                count = 0
                for icell in cells:
                    if icell.containsPoint(position):
                        if debug:
                            log.debug(icell.getVertices())

                        try:
                            tmp = self.value[icell.number]
                            if count == 0:
                                answer = list(tmp)
                            else:
                                for i in answer:
                                    answer = [x+y for x in answer for y in tmp]
                            count += 1

                        except IndexError:
                            log.error('Field::evaluate failed, inconsistent data at cell %d' % icell.label)
                            log.error(icell.getVertices())
                            raise
                # end loop over icells
                if count == 0:
                    log.error('Field::evaluate - no source cell found for position %s', str(position))
                    # for icell in cells:
                    #    log.debug(icell.number, icell.containsPoint(position), icell.glob2loc(position))
                else:
                    answer = [x/count for x in answer]
                    return answer

        else:
            # no source cell found
            log.error('Field::evaluate - no source cell found for position ' + str(position))
            raise ValueError('Field::evaluate - no source cell found for position ' + str(position))

    def getVertexValue(self, vertexID):
        """
        Returns the value associated with a given vertex.

        :param int vertexID: Vertex identifier
        :return: The value
        :rtype: Physics.PhysicalQuantity
        """
        if self.fieldType == FieldType.FT_vertexBased:
            return PhysicalQuantity(value=self.value[vertexID], unit=self.unit)
        else:
            raise TypeError('Attempt to acces vertex value of cell based field, use evaluate instead')
        
    def getCellValue(self, cellID):
        """
        Returns the value associated with a given cell.

        :param int cellID: Cell identifier
        :return: The value
        :rtype: Physics.PhysicalQuantity
        """
        if self.fieldType == FieldType.FT_cellBased:
            return PhysicalQuantity(value=self.value[cellID], unit=self.unit)
        else:
            raise TypeError('Attempt to acces cell value of vertex based field, use evaluate instead')

    def giveValue(self, componentID):
        """
        Returns the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :return: The value
        :rtype: tuple
        """
        return self.value[componentID]  

    def setValue(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :param tuple value: Value to be set for a given component, should have the same units as receiver

        .. Note:: If a mesh has mapping attached (a mesh view) then we have to remember value locally and record change. The source field values are updated after commit() method is invoked.
        """
        self.value[componentID] = value

    def commit(self):
        """
        Commits the recorded changes (via setValue method) to a primary field.
        """
    
    def getObjectID(self):
        """
        Returns field objectID.

        :return: Object's ID 
        :rtype: int
        """
        return self.objectID
    
    def getUnits(self):
        """
        :return: Returns units of the receiver
        :rtype: Physics.PhysicalUnits
        """
        return self.unit

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
        if self.fieldType == FieldType.FT_vertexBased:
            values = [0]*mesh.getNumberOfVertices()
            for v in range(self.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(self.mesh.getVertex(v).label)] = self.value[v]
            for v in range(field.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(field.mesh.getVertex(v).label)] = field.value[v]
        else:
            values = [0]*mesh.getNumberOfCells()
            for v in range(self.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(self.mesh.giveCell(v).label)] = self.value[v]
            for v in range(field.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(field.mesh.giveCell(v).label)] = field.value[v]

        self.mesh = mesh
        self.value = values

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

    def field2Image2D(self, plane='xy', elevation=(-1.e-6, 1.e-6), numX=10, numY=20, interp='linear', fieldComponent=0, vertex=True, colorBar='horizontal', colorBarLegend='', barRange=(None, None), barFormatNum='%.3g', title='', xlabel='', ylabel='', fileName='', show=True, figsize=(8, 4), matPlotFig=None):
        """ 
        Plots and/or saves 2D image using a matplotlib library. Works for structured and unstructured 2D/3D fields. 2D/3D fields need to define plane. This method gives only basic viewing options, for aesthetic and more elaborated output use e.g. VTK field export with 
        postprocessors such as ParaView or Mayavi. Idea from https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#id1

        :param str plane: what plane to extract from field, valid values are 'xy', 'xz', 'yz'
        :param tuple elevation: range of third coordinate. For example, in plane='xy' is grabs z coordinates in the range
        :param int numX: number of divisions on x graph axis
        :param int numY: number of divisions on y graph axis
        :param str interp: interpolation type when transferring to a grid. Valid values 'linear', 'nearest' or 'cubic'
        :param int fieldComponent: component of the field
        :param bool vertex: if vertices shoud be plot as points
        :param str colorBar: color bar details. Valid values '' for no colorbar, 'vertical' or 'horizontal'  
        :param str colorBarLegend: Legend for color bar. If '', current field name and units are printed. None prints nothing.
        :param tuple barRange: min and max bar range. If barRange=('NaN','NaN'), it is adjusted automatically
        :param str barFormatNum: format of color bar numbers
        :param str title: title
        :param str xlabel: x axis label
        :param str ylabel: y axis label
        :param str fileName: if nonempty, a filename is written to the disk, usually png, pdf, ps, eps and svg are supported
        :param bool show: if the plot should be showed
        :param tuple figsize: size of canvas in inches. Affects only showing a figure. Image to a file adjust one side automatically.
        :param obj matPlotFig: False means plot window remains in separate thread, True waits until a plot window becomes closed
        
        :return: handle to matPlotFig
        :rtype: matPlotFig
        """
        
        try:
            import numpy as np
            import math
            from scipy.interpolate import griddata
            import matplotlib
            matplotlib.use('TkAgg')  # Qt4Agg gives an empty, black window
            import matplotlib.pyplot as plt
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
        vertexPoints = []
        vertexValue = []
        for i in range(0, numVertices):
            coords = mesh.getVertex(i).getCoordinates()
            # print(coords)
            value = self.giveValue(i)[fieldComponent]
            
            if elevation[1] > coords[elev] > elevation[0]:
                vertexPoints.append((coords[indX], coords[indY]))
                vertexValue.append(value)
        
        if len(vertexPoints) == 0:
            log.info('No valid vertex points found, putting zeros on domain 1 x 1')
            for i in range(5):
                vertexPoints.append((i % 2, i/4.))
                vertexValue.append(0)

        # for i in range (0, len(vertexPoints)):
        #     print (vertexPoints[i], vertexValue[i])

        vertexPointsArr = np.array(vertexPoints)
        vertexValueArr = np.array(vertexValue)
        
        xMin = vertexPointsArr[:, 0].min()
        xMax = vertexPointsArr[:, 0].max()
        yMin = vertexPointsArr[:, 1].min()
        yMax = vertexPointsArr[:, 1].max()
        
        # print(xMin, xMax, yMin, yMax)
        
        grid_x, grid_y = np.mgrid[xMin:xMax:complex(0, numX), yMin:yMax:complex(0, numY)]
        grid_z1 = griddata(vertexPointsArr, vertexValueArr, (grid_x, grid_y), interp)
        
        # print (grid_z1.T)
        
        plt.ion()  # ineractive mode
        
        if matPlotFig is None:
            matPlotFig = plt.figure(figsize=figsize)
            # plt.xlim(xMin, xMax)
            # plt.ylim(yMin, yMax)
        
        plt.clf()
        plt.axis((xMin, xMax, yMin, yMax))
        image = plt.imshow(grid_z1.T, extent=(xMin, xMax, yMin, yMax), origin='lower', aspect='equal')
        # plt.margins(tight=True)
        # plt.tight_layout()
        # plt.margins(x=-0.3, y=-0.3)

        if colorBar:
            cbar = plt.colorbar(orientation=colorBar, format=barFormatNum)
            if colorBarLegend is not None:
                if colorBarLegend == '':
                    colorBarLegend = self.getFieldIDName() + '_' + str(fieldComponent)
                    if self.unit is not None:
                        colorBarLegend = colorBarLegend + ' (' + self.unit.name() + ')'
                cbar.set_label(colorBarLegend, rotation=0 if colorBar == 'horizontal' else 90)
        if title:
            plt.title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
        if vertex == 1:
            plt.scatter(vertexPointsArr[:, 0], vertexPointsArr[:, 1], marker='o', c='b', s=5, zorder=10)

        # plt.axis('equal')
        # plt.gca().set_aspect('equal', adjustable='box-forced')
        
        if isinstance(barRange[0], float) or isinstance(barRange[0], int):
            image.set_clim(vmin=barRange[0], vmax=barRange[1])

        if fileName:
            plt.savefig(fileName, bbox_inches='tight')
        if show:
            matPlotFig.canvas.draw()
            # plt.ioff()
            # plt.show(block=True)
        return matPlotFig
  
    def field2Image2DBlock(self):
        """
        Block an open window from matPlotLib. Waits until closed.
        """
        import matplotlib.pyplot as plt
        plt.ioff()
        plt.show(block=True)

    def toHdf5(self, fileName, group='component1/part1'):
        """
        Dump field to HDF5, in a simple format suitable for interoperability (TODO: document).

        :param str fileName: HDF5 file
        :param str group: HDF5 group the data will be saved under.

        The HDF hierarchy is like this::

            group
              |
              +--- mesh_01 {hash=25aa0aa04457}
              |      +--- [vertex_coords]
              |      +--- [cell_types]
              |      \--- [cell_vertices]
              +--- mesh_02 {hash=17809e2b86ea}
              |      +--- [vertex_coords]
              |      +--- [cell_types]
              |      \--- [cell_vertices]
              +--- ...
              +--- field_01
              |      +--- -> mesh_01
              |      \--- [vertex_values]
              +--- field_02
              |      +--- -> mesh_01
              |      \--- [vertex_values]
              +--- field_03
              |      +--- -> mesh_02
              |      \--- [cell_values]
              \--- ...

        where ``plain`` names are HDF (sub)groups, ``[bracketed]`` names are datasets, ``{name=value}`` are HDF attributes, ``->`` prefix indicated HDF5 hardlink (transparent to the user); numerical suffixes (``_01``, ...) are auto-allocated. Mesh objects are hardlinked using HDF5 hardlinks if an identical mesh is already stored in the group, based on hexdigest of its full data.

        .. note:: This method has not been tested yet. The format is subject to future changes.
        """
        import h5py
        hdf = h5py.File(fileName, 'a', libver='latest')
        if group not in hdf:
            gg = hdf.create_group(group)
        else:
            gg = hdf[group]
        # raise IOError('Path "%s" is already used in "%s".'%(path,fileName))

        def lowestUnused(trsf, predicate, start=1):
            """
            Find the lowest unused index, where *predicate* is used to test for existence, and *trsf* transforms
            integer (starting at *start* and incremented until unused value is found) to whatever predicate accepts
            as argument. Lowest transformed value is returned.
            """
            import itertools
            for i in itertools.count(start=start):
                t = trsf(i)
                if not predicate(t):
                    return t
        # save mesh (not saved if there already)
        newgrp = lowestUnused(trsf=lambda i: 'mesh_%02d' % i, predicate=lambda t: t in gg)
        mh5 = self.getMesh().asHdf5Object(parentgroup=gg, newgroup=newgrp)

        if self.value:
            fieldGrp = hdf.create_group(lowestUnused(trsf=lambda i, group=group: group+'/field_%02d' % i, predicate=lambda t: t in hdf))
            fieldGrp['mesh'] = mh5
            fieldGrp.attrs['fieldID'] = self.fieldID
            fieldGrp.attrs['valueType'] = self.valueType
            # string/bytes may not contain NULL when stored as string in HDF5
            # see http://docs.h5py.org/en/2.3/strings.html
            # that's why we cast to opaque type "void" and uncast using tostring before unpickling
            fieldGrp.attrs['unit'] = numpy.void(pickle.dumps(self.unit))
            fieldGrp.attrs['time'] = numpy.void(pickle.dumps(self.time))
            # fieldGrp.attrs['time']=self.time.getValue()
            if self.fieldType == FieldType.FT_vertexBased:
                val = numpy.empty(shape=(self.getMesh().getNumberOfVertices(), self.getRecordSize()), dtype=numpy.float)
                for vert in range(self.getMesh().getNumberOfVertices()):
                    val[vert] = self.getVertexValue(vert).getValue()
                fieldGrp['vertex_values'] = val
            elif self.fieldType == FieldType.FT_cellBased:
                # raise NotImplementedError("Saving cell-based fields to HDF5 is not yet implemented.")
                val = numpy.empty(shape=(self.getMesh().getNumberOfCells(), self.getRecordSize()), dtype=numpy.float)
                for cell in range(self.getMesh().getNumberOfCells()):
                    val[cell] = self.getCellValue(cell)
                fieldGrp['cell_values'] = val
            else:
                raise RuntimeError("Unknown fieldType %d." % self.fieldType)
        hdf.close() # necessary for windows

    @staticmethod
    def makeFromHdf5(fileName, group='component1/part1'):
        """
        Restore Fields from HDF5 file.

        :param str fileName: HDF5 file
        :param str group: HDF5 group the data will be read from (IOError is raised if the group does not exist).
        :return: list of new :obj:`Field` instances
        :rtype: [Field,Field,...]


        .. note:: This method has not been tested yet.
        """
        import h5py
        hdf = h5py.File(fileName, 'r', libver='latest')
        grp = hdf[group]
        # load mesh and field data from HDF5
        meshObjs = [obj for name, obj in grp.items() if name.startswith('mesh_')]
        fieldObjs = [obj for name, obj in grp.items() if name.startswith('field_')]
        # construct all meshes as mupif objects
        meshes = [mesh.Mesh.makeFromHdf5Object(meshObj) for meshObj in meshObjs]
        # construct all fields as mupif objects
        ret = []
        for f in fieldObjs:
            if 'vertex_values' in f:
                fieldType, values = FieldType.FT_vertexBased, numpy.array(f['vertex_values'])
            elif 'cell_values' in f:
                fieldType, values = FieldType.FT_cellBased, numpy.array(f['cell_values'])
            else:
                raise ValueError("HDF5/mupif format error: unable to determine field type.")
            fieldID, valueType, unit, time = FieldID(f.attrs['fieldID']), f.attrs['valueType'], f.attrs['unit'].tostring(), f.attrs['time'].tostring()
            if unit == '':
                unit = None  # special case, handled at saving time
            else:
                unit = pickle.loads(unit)
            if time == '':
                time = None  # special case, handled at saving time
            else:
                time = pickle.loads(time)
           
            meshIndex = meshObjs.index(f['mesh'])  # find which mesh object this field refers to
            ret.append(Field(mesh=meshes[meshIndex], fieldID=fieldID, unit=unit, time=time, valueType=valueType, value=values, fieldType=fieldType))
        hdf.close() # necessary for windows
        return ret


    def toMeshioMesh(self):
        return Field.manyToMeshioMesh([self])

    @staticmethod
    # @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def manyToMeshioMesh(
        fields: typing.Sequence[mupif.Field]
    ) -> typing.List[mupif.Field]:
        import meshio
        if len(fields)==0: raise ValueError('fields must not be enpty.')
        if len(set([f.getMesh() for f in fields]))!=1: raise RuntimeError('All fields must share the same mupif.Mesh.')
        msh=fields[0].getMesh()
        points=msh.getVertices()
        cell_data,point_data={},{}
        # defined here: https://github.com/nschloe/meshio/blob/6a1b8c4c3db24ea788a8cac00e46c7f9d562e4d0/meshio/_common.py#L189
        points,cells_list=msh.toMeshioPointsCells()
        for f in fields:
            assert f.getFieldType() in (FieldType.FT_vertexBased, FieldType.FT_cellBased)
            ptData=(f.getFieldType()==FieldType.FT_vertexBased)
            rows=(msh.getNumberOfVertices() if ptData else msh.getNumberOfCells())
            cols=f.getRecordSize()
            dta=np.ndarray((rows,cols),dtype='float32')
            dta=np.array([f.giveValue(row) for row in range(rows)])
            (point_data if ptData else cell_data)[f.getFieldIDName()]=(dta if ptData else dta.T)
            #print(f.getFieldIDName())
            #print('Is point data?',ptData)
            #print(f.getFieldIDName(),dta.shape)
        return meshio.Mesh(points,cells_list,point_data,cell_data)

    def makeFromMeshioMesh(
            input: typing.Union[str,meshio.Mesh], # could also be buffer, is that useful?
            unit: dict[str,PhysicalUnit], # maps field name to PhysicalUnit
            time: PhysicalQuantity=PhysicalQuantity(value=0,unit='s')
        ) -> typing.List[Field]:
        if isinstance(input,str):
            input=meshio.read(input)
        msh=mesh.Mesh.makeFromMeshioPointsCells(input.points,input.cells)
        ret=[]
        for data,fieldType in (input.point_data,FieldType.FT_vertexBased),(input.cell_data,FieldType.FT_cellBased):
            for fname,values in data.items():
                # reshape scalar array saved as 1D
                if len(values.shape)==1: values=np.reshape(values,(-1,1))
                ret.append(Field(
                    mesh=msh,
                    fieldID=FieldID[fname],
                    unit=unit.get(fname,None),
                    time=time,
                    valueType=ValueType.fromNumberOfComponents(values.shape[1]),
                    value=values,
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

