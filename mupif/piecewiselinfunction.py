from . import data
import Pyro5.api
import typing
import pydantic
import numpy as np

from .units import Unit, Quantity, RefQuantity, U
from .dataid import DataID
from .property import ConstantProperty
from .mupifquantity import ValueType
from .dbrec import DbDictable
from .function import Function


@Pyro5.api.expose
class PiecewiseLinFunction(Function, DbDictable):
    """

    .. automethod:: __init__
    """

    x: Quantity
    y: Quantity

    def __init__(self, *, metadata={}, **kw):
        x = kw['x']
        y = kw['y']
        if 'valueType' in kw:
            del kw['valueType']
        if 'unit' in kw:
            del kw['unit']
        if 'inputs' in kw:
            del kw['inputs']
        if 'metadata' in kw:
            del kw['metadata']
        super().__init__(
            metadata=metadata,
            inputs={"x": {
                "valueType": ValueType.getValueFromQuantity(x[0]),
                "unit": x.unit
            }},
            valueType=ValueType.getValueFromQuantity(y[0]),
            unit=y.unit,
            **kw)
        defaults = dict([
            ('Type', 'mupif.Function'),
        ])
        for k, v in defaults.items():
            if k not in metadata:
                self.updateMetadata(dict(k=v))
        if ValueType.getValueFromQuantity(x[0]) is not ValueType.Scalar:
            raise ValueError("Only Scalar X is allowed")
        if self.valueType is not ValueType.Scalar:
            raise ValueError("Only Scalar Y is now allowed")

    def evaluate(self, p):
        value_data = np.interp(x=p['x'], xp=self.x, fp=self.y)
        return ConstantProperty(value=value_data, propID=self.dataID, valueType=self.valueType, unit=self.unit)

    def to_db_dict_impl(self):
        return {
            'ClassName': 'PiecewiseLinFunction',
            'DataID': self.dataID.name,
            'X': self.x,
            'Y': self.y
        }

    @staticmethod
    def from_db_dict(d):
        return PiecewiseLinFunction(
            x=d['X'],
            y=d['Y'],
            dataID=DataID[d['DataID']]
        )