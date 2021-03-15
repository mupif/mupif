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
from .value import ValueType
from . import bbox
from . import apierror
from . import mupifobject
from .dataid import FieldID
from . import cellgeometrytype
#import mupif.mesh
from . import mesh
from . import value
from .units import Quantity, Unit

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
class Field(value.Value):
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
    #: Field type (displacement, strain, temperature ...)
    fieldID: FieldID
    #: Time associated with field values
    time: Quantity
    #: whether the field is vertex-based or cell-based
    fieldType: FieldType=FieldType.FT_vertexBased
    #: Optional ID of problem object/subdomain to which field is related, default = 0
    objectID: int=0

    def __init__(self,**kw):
        super().__init__(**kw) # this calls the real ctor
        # fix zero values
        if 1:
            if len(self.quantity)==0:
                if self.fieldType==FieldType.FT_vertexBased: ncomp=self.mesh.getNumberOfVertices()
                else: ncomp=self.mesh.getNumberOfCells()
                self.quantity=Quantity(value=np.zeros((ncomp,self.valueType.getNumberOfComponents())),unit=self.quantity.unit)
        # add some extra metadata
        self.updateMetadata({
            'Units':self.getUnit().to_string(),
            'Type':'mupif.field.Field',
            'Type_ID':str(self.fieldID),
            'FieldType':str(self.fieldType),
            'ValueType':str(self.valueType)
        })



    def getMesh(self):
        """
        Obtain mesh.

        :return: Returns a mesh of underlying discretization
        :rtype: mesh.Mesh
        """
        return self.mesh

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
        :rtype: Physics.Quantity
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
        :rtype: Physics.Quantity with given value or tuple of values
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
        :rtype: Physics.Quantity
        """
        if self.fieldType == FieldType.FT_vertexBased:
            return  Quantity(value=self.getRecord(vertexID), unit=self.getUnit())
        else:
            raise TypeError('Attempt to acces vertex value of cell based field, use evaluate instead')
        
    def getCellValue(self, cellID):
        """
        Returns the value associated with a given cell.

        :param int cellID: Cell identifier
        :return: The value
        :rtype: Physics.Quantity
        """
        if self.fieldType == FieldType.FT_cellBased:
            return Quantity(value=self.getRecord(cellID), unit=self.getUnit())
        else:
            raise TypeError('Attempt to acces cell value of vertex based field, use evaluate instead')

    def getObjectID(self):
        """
        Returns field objectID.

        :return: Object's ID 
        :rtype: int
        """
        return self.objectID

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
            values=np.zeros_like(self.quantity,shape=(mesh.getNumberOfVertices(),self.getRecordSize()))
            #values = [0]*mesh.getNumberOfVertices()
            for f in self,field:
                for v in range(f.mesh.getNumberOfVertices()):
                    values[mesh.vertexLabel2Number(f.mesh.getVertex(v).label)] = f.getRecord(v)
        else:
            # values = [0]*mesh.getNumberOfCells()
            values=np.zeros_like(self.quantity,shape=(mesh.getNumberOfCells(),self.getRecordSize()))
            for f in self,field:
                for v in range(f.mesh.getNumberOfCells()):
                    values[mesh.cellLabel2Number(f.mesh.giveCell(v).label)] = f.getRecord(v)

        self.mesh = mesh
        self.quantity = values

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

    def plot2D(self, plane="xy", title=None, fieldComponent=0, warpField=None, warpScale=0., fileName=None, show=0, colorbar='horizontal'):
        """ 
        Plots and/or saves 2D image using a matplotlib library. Works for structured and unstructured 2D/3D fields. 2D/3D fields need to define plane. This method gives only basic viewing options, for aesthetic and more elaborated output use e.g. VTK field export with 
        postprocessors such as ParaView or Mayavi. Idea from https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#id1

        :param str plane: what plane to extract from field, valid values are 'xy', 'xz', 'yz'
        :param int fieldComponent: component of the field
        :param bool vertex: if vertices shoud be plot as points
        :param str colorBar: color bar details. Valid values '' for no colorbar, 'vertical' or 'horizontal'  
        :param str title: title
        :param str fileName: if nonempty, a filename is written to the disk, usually png, pdf, ps, eps and svg are supported
        :param bool show: if the plot should be showed
        :param tuple figsize: size of canvas in inches. Affects only showing a figure. Image to a file adjust one side automatically.
        :param Field warpField: vector field to wrap geometry
        :param float warpScale: warping scale
        :return: handle to matplotlib figure
        """
        import numpy as np
        import math
        from scipy.interpolate import griddata
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
        vx=[]
        vy=[]
        vertexValue = []
        for i in range(0, numVertices):
            coords = mesh.getVertex(i).getCoordinates()
            if (warpField):
                #coords+=warpField.evaluate(coords).getValue()*warpScale
                warpVec =  (warpScale * s for s in warpField.evaluate(coords).getValue())
                coords = tuple(map(lambda x, y: x + y, coords,warpVec))
            #print(coords)
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

        #v = np.array(vertexPoints)
        #vertexValueArr = np.array(vertexValue)
        
        xMin = min(vx)
        xMax = max(vx)
        yMin = min(vy)
        yMax = max(vy)
        
        #print(xMin, xMax, yMin, yMax)
        
        # Create the Triangulation; no triangles so Delaunay triangulation created.
        triang = matplotlib.tri.Triangulation(vx, vy)
        # pcolor plot.
        plt.figure()
        plt.gca().set_aspect('equal')
        plt.tricontourf(triang, vertexValue)
        if (colorbar):
            plt.colorbar(orientation=colorbar)
        plt.tricontour(triang, vertexValue, colors='k')
        plt.scatter(vx, vy, marker='o', c='k', s=1, zorder=10)
        if title:
            plt.title(title)    
        if fileName:
            plt.savefig(fileName, bbox_inches='tight')
        #if show:
        #    matPlotFig.canvas.draw()
        #return plt

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

        if len(self.value)>0:
            fieldGrp = hdf.create_group(lowestUnused(trsf=lambda i, group=group: group+'/field_%02d' % i, predicate=lambda t: t in hdf))
            fieldGrp['mesh'] = mh5
            fieldGrp.attrs['fieldID'] = self.fieldID
            fieldGrp.attrs['valueType'] = self.valueType
            # string/bytes may not contain NULL when stored as string in HDF5
            # see http://docs.h5py.org/en/2.3/strings.html
            # that's why we cast to opaque type "void" and uncast using tostring before unpickling
            fieldGrp.attrs['unit'] = numpy.void(pickle.dumps(self.getUnit()))
            fieldGrp.attrs['time'] = numpy.void(pickle.dumps(self.time))
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
            ret.append(Field(mesh=meshes[meshIndex], fieldID=fieldID, unit=unit, time=time, valueType=valueType, value=values.tolist(), fieldType=fieldType))
        hdf.close() # necessary for windows
        return ret


    def toMeshioMesh(self):
        return Field.manyToMeshioMesh([self])

    @staticmethod
    # @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def manyToMeshioMesh(
        fields: typing.Sequence[Field]
    ) -> typing.List[Field]:
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
            # sys.stderr.write(f'each record has {cols} components\n')
            # dta=np.ndarray((rows,cols),dtype='float32')
            dta=np.array([f.getRecord(row) for row in range(rows)])
            (point_data if ptData else cell_data)[f.getFieldIDName()]=(dta if ptData else dta.T)
            #print(f.getFieldIDName())
            #print('Is point data?',ptData)
            #print(f.getFieldIDName(),dta.shape)
        return meshio.Mesh(points,cells_list,point_data,cell_data)

    def makeFromMeshioMesh(
            input: typing.Union[str,meshio.Mesh], # could also be buffer, is that useful?
            unit: dict[str,Unit], # maps field name to Unit
            time: Quantity=Quantity(value=0,unit='s')
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

