"""
Enumeration defining supported types of field and property values, e.g. scalar, vector, tensor
"""
from enum import IntEnum

from . import units
from . import data
import typing
import pydantic
import warnings
import numpy as np


class ValueType(IntEnum):
    Scalar = 1
    Vector = 2
    Tensor = 3
    # the following values should not be used in common cases
    ScalarArray = 4
    VectorArray = 5
    TensorArray = 6

    @staticmethod
    def getValueFromQuantity(q):
        shape = q.value.shape
        dimension = len(shape)
        if dimension == 0:
            return ValueType.Scalar
        if dimension == 1:
            return ValueType.Vector
        if dimension == 2:
            return ValueType.Tensor
        return None

    def getNumberOfComponents(self):  # this function is probably no longer valid
        return {ValueType.Scalar: 1, ValueType.Vector: 3, ValueType.Tensor: 9}[self]

    @staticmethod
    def fromNumberOfComponents(i):  # this function is probably no longer valid
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


class MupifQuantity(data.Data):
    """
    Abstract base class for representing a quantity, common parent class for
    :obj:`Field` and :obj:`Property` classes. Quantity means value and an
    associated unit.

    The quantity itself can be accessed as `MupifQuantity.quantity` (or `.q` as
    shorthand) and can be used for unit-aware arithmetics.

    Value and unit can be accessed separately as `value` and `unit`.
    """

    quantity: typing.Union[units.Quantity, units.RefQuantity]
    valueType: ValueType = ValueType.Scalar

    # shorthand accessor for quantity (less typing)
    @property
    def q(self): return self.quantity
    # access value and unit directly
    @property
    def value(self): return self.quantity.value
    @property
    def unit(self): return self.quantity.unit

    def __init__(self, value=None, unit=None, **kw):
        if value is not None or unit is not None:
            given = (['value'] if value is not None else [])+(['unit'] if unit is not None else [])+(['quantity'] if 'quantity' in kw else [])
            if value is None or unit is None or 'quantity' in kw:
                raise ValueError(f'Must specify only either quantity=, or both value= and unit= (given: {", ".join(given)})')
            # warnings.warn("Field(value=...) is deprecated, use Field(quantity=...) instead.")
            kw['quantity'] = units.Quantity(value=value, unit=unit)
        super().__init__(**kw)  # this calls the real ctor

    def getValue(self): return self.quantity.value

    def getQuantity(self): return self.quantity

    def getValueType(self):
        """
        Returns ValueType of the field, e.g. scalar, vector, tensor.

        :return: Returns value type of the receiver
        :rtype: ValueType
        """
        return self.valueType

    def getUnit(self) -> units.Unit:
        """
        Returns representation of property units.
        """
        return self.quantity.unit

    def dataDigest(self, *args):
        def numpyHash(*_args):
            """Return concatenated hash (hexdigest) of all args, which must be numpy arrays. This function is used to
            find an identical mesh which was already stored."""
            import hashlib
            # print(f'{_args=}')
            H = hashlib.sha1()
            for arr in _args:
                H.update(arr.view(np.uint8))
            return H.hexdigest()
        return numpyHash(self.quantity.value, np.frombuffer(bytes(self.quantity.unit), dtype=np.uint8), *args)
