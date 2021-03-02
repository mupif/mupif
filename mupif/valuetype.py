"""
Enumeration defining supported types of field and property values, e.g. scalar, vector, tensor
"""
from enum import IntEnum


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
