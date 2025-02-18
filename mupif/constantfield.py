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
import Pyro5.api
import logging
from . import field
from . import bbox
from . import dataid
from . import mupifquantity
from . import units
from pydantic.dataclasses import dataclass

log = logging.getLogger()

# debug flag
debug = 0


@Pyro5.api.expose
class ConstantField(field.Field):  # TODO implement all abstract methods
    """
    Representation of field with constant value. Field is a scalar, vector, or tensorial
    quantity defined on a spatial domain. 

    .. automethod:: _evaluate
    """

    def evaluate(self, positions, eps=0.0):
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
            answer = []
            for pos in positions:
                answer.append(self._evaluate(pos, eps))
            return units.Quantity(value=answer, unit=self.unit)
        else:
            # single position passed
            return units.Quantity(value=self._evaluate(positions, eps), unit=self.unit)

    def _evaluate(self, position, eps):
        """
        Evaluates the receiver at a single spatial position.

        :param tuple position: 1D/2D/3D position vector
        :param float eps: Optional tolerance
        :return: field value
        :rtype: tuple  of doubles 

        .. note:: This method has some issues related to https://sourceforge.net/p/mupif/tickets/22/ .
        """
        if self.mesh:  # if mesh provide, check if inside
            cells = self.mesh.giveCellLocalizer().giveItemsInBBox(bbox.BBox([c-eps for c in position], [c+eps for c in position]))
            if len(cells):
                return self.value
            else:
                # no source cell found
                log.error('Field::evaluate - no source cell found for position ' + str(position))
                raise ValueError('Field::evaluate - no source cell found for position ' + str(position))
        else:
            return self.value

    def getVertexValue(self, vertexID):
        """
        Returns the value associated with a given vertex.

        :param int vertexID: Vertex identifier
        :return: The value
        :rtype: Physics.PhysicalQuantity
        """
        return self.value
        
    def getCellValue(self, cellID):
        """
        Returns the value associated with a given cell.

        :param int cellID: Cell identifier
        :return: The value
        :rtype: Physics.PhysicalQuantity
        """
        return self.value

    def _giveValue(self, componentID):
        """
        Returns the value associated with a given component (vertex or cell).
        Depreceated, use getVertexValue() or getCellValue()

        :param int componentID: An identifier of a component: vertexID or cellID
        :return: The value
        :rtype: Physics.PhysicalQuantity
        """
        return units.Quantity(value=self.value, unit=self.unit)
    
    def giveValue(self, componentID):
        """
        Returns the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :return: The value
        :rtype: tuple
        """
        return self.value    

    def setValue(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :param tuple value: New value of the receiver (tuple)
        """
        self.value = value

    def merge(self, field):
        """
        Merges the receiver with given field together. Both fields should be on different parts of the domain (can also overlap), but should refer to same underlying discretization, otherwise unpredictable results can occur.

        :param Field field: given field to merge with.
        """
        raise TypeError("Field::merge: merging constant field not supported")


if __name__ == '__main__':
    cf = ConstantField(mesh=None, fieldID=dataid.DataID.FID_Temperature, valueType=mupifquantity.ValueType.Scalar, unit=units.U['degC'], time=0.0, values=(15.,))
    ans = cf.evaluate((10, 0, 0))
    print(ans)
