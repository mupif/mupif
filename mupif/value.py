"""
Enumeration defining supported types of field and property values, e.g. scalar, vector, tensor
"""
from enum import IntEnum

from . import dumpable
from . import units
from . import mupifobject
import typing
import deprecated
import pydantic
import numpy as np


class ValueType(IntEnum):
    Scalar = 1
    Vector = 2
    Tensor = 3

    def getNumberOfComponents(self):
        return {ValueType.Scalar:1,ValueType.Vector:3,ValueType.Tensor:9}[self]

    @staticmethod
    def fromNumberOfComponents(i):
        """
        :param int i: number of components
        :return: value type corresponding to the number of components

        RuntimeError is raised if *i* does not match any value known.
        """
        if i == 1:
            return ValueType.Scalar
        elif i == 3:
            return ValueType.Vector
        elif i == 9:
            return ValueType.Tensor
        else:
            raise RuntimeError('No ValueType with %i components' % i)



class Value(mupifobject.MupifObject):

    unit: units.Unit
    value: dumpable.NumpyArrayFloat64=pydantic.Field(default_factory=lambda: np.array([]))
    valueType: ValueType=ValueType.Scalar

    @pydantic.validator('value',pre=True,always=True)
    def convert_value(cls,v):
        if isinstance(v,np.ndarray): return v
        return np.array(v)

    def getValueType(self):
        """
        Returns ValueType of the field, e.g. scalar, vector, tensor.

        :return: Returns value type of the receiver
        :rtype: ValueType
        """
        return self.valueType

    def setRecord(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or cell).

        :param int componentID: An identifier of a component: vertexID or cellID
        :param tuple value: Value to be set for a given component, should have the same units as receiver
        """
        self.value[componentID] = value

    def getRecord(self, componentID):
        """
        Returns the value of property in a tuple.
        :param Physics.Quantity time: Time of property evaluation
        :param \**kwargs: Arbitrary keyword arguments, see documentation of derived classes.

        :return: Property value as an array
        :rtype: tuple
        """
        return self.value[componentID]


    def getRecordSize(self):
        """
        Return the number of scalars per value, depending on :obj:`valueType` passed when constructing the instance.

        :return: number of scalars (1,3,9 respectively for scalar, vector, tensor)
        :rtype: int
        """
        return self.valueType.getNumberOfComponents()

    @deprecated.deprecated('use Value.getUnit instead.')
    def getUnits(self):
        return self.getUnit()

    def getUnit(self) -> units.Unit:
        """
        Returns representation of property units.
        """
        return self.unit
