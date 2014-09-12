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
import BBox
import Cell
import FieldID
import ValueType
from numpy import array, arange, random, zeros
import copy

#debug flag
debug = 0

class FieldType:
    """
    Represent the supported values of FieldType. 
    """
    FT_vertexBased = 1
    FT_cellBased   = 2


class Field:
    """
    Representation of field. Field is a scalar, vector, or tensorial 
    quantity defined on spatial domain. The field, however is assumed
    to be fixed in time. The field can be evaluated in any spatial point 
    belonging to underlying domain. 

    Derived classes will implement fields defined on common discretizations, 
    like fields defined on structured/unstructured FE meshes, FD grids, etc.
    """
    def __init__(self, mesh, fieldID, valueType, units, time, values=None, fieldType=FieldType.FT_vertexBased):
        """
        Initializes the field instance.

        ARGS:
            mesh(Mesh): Instance of Mesh class representing underlying discretization.
            fieldID(FieldID): field type
            valueType(ValueType): type of field values 
            units: units of the field values
            time(double): time
            values(tuple): field values (format dependent of particular field type)
            fieldType(FieldType): determines field type (vaues specified as vertex or cell values)
        """
        self.mesh = mesh
        self.fieldID = fieldID
        self.valueType = valueType
        self.time = time
        self.units = units
        self.uri = None   #pyro uri; used in distributed setting
        self.fieldType = fieldType
        if values == None:
            ncomponents = mesh.getNumberOfVertices()
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

    def getMesh(self):
        """
        Returns representation of underlying discretization.
        RETURNS:
            Mesh
        """
        return self.mesh

    def getValueType(self):
        """
        Returns value type (ValueType) of the receiver.
        """
        return self.valueType

    def getFieldID(self):
        """
        Returns field ID (FieldID type).
        """
        return self.fieldID

    def evaluate(self, position, eps=0.001):
        """
        Evaluates the receiver at given spatial position.

        ARGS:
            position (tuple): 3D position vector
            eps(double): Optional tolerance
        RETURNS:
            tuple. 
        """
        cells = self.mesh.giveCellLocalizer().giveItemsInBBox(BBox.BBox([ c-eps for c in position], [c+eps for c in position]))
        if len(cells):
            for icell in cells:
                try:
                    if icell.containsPoint(position):
                        if debug:
                            print icell.getVertices() 
                                                    
                        if (self.fieldType == FieldType.FT_vertexBased):
                            answer = icell.interpolate(position, [self.values[i.number] for i in icell.getVertices()])
                        else:
                            answer = self.values[icell.number]
                        return answer

                except ZeroDivisionError:
                    print icell.number, position,
                    cell.debug=1
                    print icell.containsPoint(position), icell.glob2loc(position)

            print "Field evaluate -no source cell found for position ",position
            for icell in cells:
                print icell.number, icell.containsPoint(position), icell.glob2loc(position)

            raise ValueError
                
        else:
            #no source cell found
            print "Field evaluate - no source cell found for position ",position
            raise ValueError

    def giveValue(self, componentID):
        """
        Returns the value associated to given component (vertex or cell IP).
        ARGS:
            componentID(tuple): identifies the component (vertexID,) or (CellID, IPID)
        """
        return self.values[componentID]

    def setValue(self, componentID, value):
        """
        Sets the value associated to given component (vertex or cell IP).
        ARGS:
            componentID(tuple):  The componentID is a tuple: (vertexID,) or (CellID, IPID)
            value(tuple):        Value to be set for given component
        NOTE:
            If mesh has mapping attached (a mesh view) then we have to remember value 
            locally and record change.
            The source field values are updated after commit() method is invoked.
        """
        self.values[componentID] = value

    def commit(self):
        """
        Commits the recorded changes (via setValue method) to primary field.
        """
    def getUnits(self):
        """
        Returns units of the receiver.
        """
        return self.units

    def merge(self, field):
        """
        Merges the receiver with given field together. 
        Both fields should be on different parts of the domain (can also overlap),
        but should refer to same underlying discretization, 
        otherwise unpredictable results can occur.
        """
        # first merge meshes 
        mesh = copy.deepcopy(self.mesh)
        mesh.merge(field.mesh)
        print mesh
        # merge the field values 
        # some type checking first
        if (self.field_type != field.field_type):
            raise TypeError("Field::merge: field_type of receiver and parameter is different")
        if (self.fieldType == FieldType.FT_vertexBased):
            values=[0]*mesh.getNumberOfVertices()
            for v in xrange(self.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(self.mesh.getVertex(v).label)]=self.values[v]
            for v in xrange(field.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(field.mesh.getVertex(v).label)]=field.values[v]
        else:
            values=[0]*mesh.giveNumberOfCells()
            for v in xrange(self.mesh.giveNumberOfCells()):
                values[mesh.cellLabel2Number(self.mesh.giveCell(v).label)]=self.values[v]
            for v in xrange(field.mesh.giveNumberOfCells()):
                values[mesh.cellLabel2Number(field.mesh.giveCell(v).label)]=field.values[v]

        self.mesh=mesh
        self.values=values


    def field2VTKData (self):
        """
        Returns VTK representation of the receiver. Useful for visualization.
        RETURNS:
            VTKDataSource
        """
        import pyvtk
        if (self.fieldType == FieldType.FT_vertexBased):
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Scalars([val[0] for val in self.values])),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Vectors(self.values)),
                                     'Unstructured Grid Example')
        else:
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Scalars([val[0] for val in self.values])),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Vectors(self.values)),
                                     'Unstructured Grid Example')
            
            
