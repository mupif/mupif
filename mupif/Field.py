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
from __future__ import print_function
from builtins import range
from builtins import object
from . import Cell
from . import FieldID
from . import ValueType
from . import BBox
from numpy import array, arange, random, zeros
import copy
try:
   import cPickle as pickle #faster serialization if available
except:
   import pickle
#import logging - never use it here, it causes cPickle.PicklingError: Can't pickle <type 'thread.lock'>: attribute lookup thread.lock failed

#debug flag
debug = 0

class FieldType(object):
    """
    Represent the supported values of FieldType, i.e. FT_vertexBased or FT_cellBased. 
    """
    FT_vertexBased = 1
    FT_cellBased   = 2


class Field(object):
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
    def __init__(self, mesh, fieldID, valueType, units, time, values=None, fieldType=FieldType.FT_vertexBased):
        """
        Initializes the field instance.

        :param Mesh mesh: Instance of a Mesh class representing the underlying discretization
        :param FieldID fieldID: Field type (displacement, strain, temperature ...)
        :param ValueType valueType: Type of field values (scalear, vector, tensor)
        :param obj units: Units of the field values
        :param float time: Time associated with field values
        :param tuple values: Field values (format dependent on a particular field type)
        :param FieldType fieldType: Optional, determines field type (values specified as vertex or cell values), default is FT_vertexBased
        """
        self.mesh = mesh
        self.fieldID = fieldID
        self.valueType = valueType
        self.time = time
        self.units = units
        self.uri = None   #pyro uri; used in distributed setting
        #self.logger = logging.getLogger()
        self.fieldType = fieldType
        if values == None:
            if (self.fieldType == FieldType.FT_vertexBased):
                ncomponents = mesh.getNumberOfVertices()
            else:
                ncomponents = mesh.getNumberOfCells()

            if valueType == ValueType.Scalar:
                recsize = 1
            elif valueType == ValueType.Vector:
                recsize = 3
            elif valueType == ValueType.Tensor:
                recsize = 9
            else:
                raise TypeError("Unknown valueType")
            self.values=zeros((ncomponents, recsize))
        else:
            self.values = values

    @classmethod
    def loadFromLocalFile(cls,fileName):
        """
        Alternative constructor from a Pickle module

        :param str fileName: File name

        :return: Returns Field instance
        :rtype: Field
        """
        return pickle.load(file(fileName,'r'))

    def getMesh(self):
        """
        :return: Returns a mesh of underlying discretization
        :rtype: Mesh
        """
        return self.mesh

    def getValueType(self):
        """
        :return: Returns value type of the receiver
        :rtype: ValueType
        """
        return self.valueType

    def getFieldID(self):
        """
        :return: Returns field ID
        :rtype: FieldID
        """
        return self.fieldID

    def getTime(self):
        """
        :return: Time of field data
        :rtype: float
        """
        return self.time

    def evaluate(self, positions, eps=0.001):
        """
        Evaluates the receiver at given spatial position(s).

        :param position: 1D/2D/3D position vectors
        :type position: tuple, a list of tuples
        :param float eps: Optional tolerance, default 0.001
        :return: field value(s)
        :rtype: tuple or a list of tuples
        """
        # test if positions is a list of positions
        if isinstance(positions, list):
            ans=[]
            for pos in positions:
                ans.append(self._evaluate(pos, eps))
            return ans
        else:
            # single position passed
            return self._evaluate(positions, eps)

    def _evaluate(self, position, eps=0.001):
        """
        Evaluates the receiver at a single spatial position.

        :param tuple position: 1D/2D/3D position vector
        :param float eps: Optional tolerance, default 0.001
        :return: field value
        :rtype: tuple
        """
        cells = self.mesh.giveCellLocalizer().giveItemsInBBox(BBox.BBox([ c-eps for c in position], [c+eps for c in position]))
        if len(cells):
            for icell in cells:
                try:
                    if icell.containsPoint(position):
                        if debug:
                            print (icell.getVertices())

                        if (self.fieldType == FieldType.FT_vertexBased):
                            try:
                                answer = icell.interpolate(position, [self.values[i.number] for i in icell.getVertices()])
                            except IndexError:
                                print ("Field::evaluate failed, inconsistent data at cell %d"%(icell.label))
                                raise
                        else:
                            answer = self.values[icell.number]
                        return answer

                except ZeroDivisionError:
                    print (icell.number, position)
                    cell.debug=1
                    print (icell.containsPoint(position), icell.glob2loc(position))

            print ("Field::evaluate - no source cell found for position ",position)
            for icell in cells:
                print (icell.number, icell.containsPoint(position), icell.glob2loc(position))

            raise ValueError

        else:
            #no source cell found
            print ("Field::evaluate - no source cell found for position ", position)
            raise ValueError("Field::evaluate - no source cell found for position "+str(position))

    def giveValue(self, componentID):
        """
        Returns the value associated with a given component (vertex or integration point on a cell).

        :param tuple componentID: A tuple identifying a component: vertex (vertexID,) or integration point (CellID, IPID)
        :return: The value
        :rtype: tuple
        """
        return self.values[componentID]

    def setValue(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or integration point on a cell).

        :param tuple componentID: A tuple identifying a component: vertex (vertexID,) or integration point (CellID, IPID)
        :param tuple value: Value to be set for a given component

        .. Note:: If a mesh has mapping attached (a mesh view) then we have to remember value locally and record change. The source field values are updated after commit() method is invoked.
        """
        self.values[componentID] = value

    def commit(self):
        """
        Commits the recorded changes (via setValue method) to a primary field.
        """
    def getUnits(self):
        """
        :return: Returns units of the receiver
        :rtype: obj
        """
        return self.units

    def merge(self, field):
        """
        Merges the receiver with given field together. Both fields should be on different parts of the domain (can also overlap), but should refer to same underlying discretization, otherwise unpredictable results can occur.

        :param Field field: given field to merge with.
        """
        # first merge meshes 
        mesh = copy.deepcopy(self.mesh)
        mesh.merge(field.mesh)
        print (mesh)
        # merge the field values 
        # some type checking first
        if (self.field_type != field.field_type):
            raise TypeError("Field::merge: field_type of receiver and parameter is different")
        if (self.fieldType == FieldType.FT_vertexBased):
            values=[0]*mesh.getNumberOfVertices()
            for v in range(self.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(self.mesh.getVertex(v).label)]=self.values[v]
            for v in range(field.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(field.mesh.getVertex(v).label)]=field.values[v]
        else:
            values=[0]*mesh.getNumberOfCells()
            for v in range(self.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(self.mesh.giveCell(v).label)]=self.values[v]
            for v in range(field.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(field.mesh.giveCell(v).label)]=field.values[v]

        self.mesh=mesh
        self.values=values

    def field2VTKData (self,name=None,lookupTable=None):
        """
        Creates VTK representation of the receiver. Useful for visualization.

        :param str name: human-readable name of the field
        :param pyvtk.LookupTable lookupTable: color lookup table
        :return: Instance of pyvtk
        :rtype: pyvtk
        """
        import pyvtk

        if name is None:
            try: name=FieldID.FID_names[self.getFieldID()] # try human-readable name
            except: name=str(self.getFieldID()) # if that fails, use number
        if lookupTable and not isinstance(lookupTable,pyvtk.LookupTable):
            # FIXME: move to some mupif-wide logger?
            print('ignoring lookupTable which is not a pyvtk.LookupTable instance.')
            lookupTable=None
        if lookupTable is None:
            lookupTable=pyvtk.LookupTable([(0,.231,.298,.752),(.4,.865,.865,.865),(.8,.706,.016,.149)],name='coolwarm')
        # see http://cens.ioc.ee/cgi-bin/cvsweb/python/pyvtk/examples/example1.py?rev=1.3 for an example
        scalarsKw=dict(name=name,lookup_table=lookupTable.name)
        vectorsKw=dict(name=name) # vectors don't have a lookup_table

        if (self.fieldType == FieldType.FT_vertexBased):
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Scalars([val[0] for val in self.values],**scalarsKw),lookupTable),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Vectors(self.values,**vectorsKw),lookupTable),
                                     'Unstructured Grid Example')
        else:
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Scalars([val[0] for val in self.values],**scalarsKw),lookupTable),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Vectors(self.values,**vectorsKw),lookupTable),
                                     'Unstructured Grid Example')

    def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
        """
        Dump Field to a file using Pickle module

        :param str fileName: File name
        :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
        """
        pickle.dump(self, file(fileName,'w'), protocol)


#    def __deepcopy__(self, memo):
#        """ Deepcopy operatin modified not to include attributes starting with underscore.
#            These are supposed to be the ones valid only to s specific copy of the receiver.
#            An example of these attributes are _PyroURI (injected by Application), 
#            where _PyroURI contains the URI of specific object, the copy should receive  
#            its own URI
#        """
#        cls = self.__class__
#        dpcpy = cls.__new__(cls)
#
#        memo[id(self)] = dpcpy
#        for attr in dir(self):
#            if not attr.startswith('_'):
#                value = getattr(self, attr)
#                setattr(dpcpy, attr, copy.deepcopy(value, memo))
#        return dpcpy


