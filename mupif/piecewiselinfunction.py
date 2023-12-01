from . import data
import Pyro5.api
import typing
import pydantic
import numpy as np

from .units import Unit
from .dataid import DataID
from .property import ConstantProperty
from .mupifquantity import ValueType
from .dbrec import DbDictable


@Pyro5.api.expose
class PiecewiseLinFunction(data.Data, DbDictable):
    """

    .. automethod:: __init__
    """

    x: typing.List[float] = []
    x_unit: Unit = None
    y: typing.List[float] = []
    y_unit: Unit = None
    data_id: DataID = DataID.ID_None
    value_type: ValueType = ValueType.Scalar

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)
        defaults = dict([
            ('Type', 'mupif.PiecewiseLinFunction'),
        ])
        for k, v in defaults.items():
            if k not in metadata:
                self.updateMetadata(dict(k=v))
        if self.value_type is not ValueType.Scalar:
            raise ValueError("Only Scalar is now allowed")

    # def setXData(self, values, unit):
    #     if len(self.y) == 0 or len(self.x) == len(values):
    #         self.x = values
    #         self.x_unit = unit
    #     else:
    #         raise SyntaxError("Size of X axis cannot be changed after adding Y data.")
    #
    # def setYData(self, values, value_type):
    #     if len(self.x) == 0 or self.x_unit is None:
    #         raise SyntaxError("X axis must be defined before adding Y axis values")
    #     elif len(self.x) != len(values):
    #         raise ValueError("Y data must have equal size as the X data.")
    #     else:
    #         self.y = values
    #         self.value_type = value_type

    def evaluate(self, x):
        x_float = x.inUnitsOf(self.x_unit).value
        value_data = np.interp(x=x_float, xp=self.x, fp=self.y)
        return ConstantProperty(value=value_data, propID=self.data_id, valueType=self.value_type, unit=self.y_unit)

    def to_db_dict_impl(self):
        return {
            'ClassName': 'PiecewiseLinFunction',
            'ValueType': self.value_type.name,
            'DataID': self.data_id.name,
            'UnitX': str(self.x_unit),
            'UnitY': str(self.y_unit),
            'X': self.x,
            'Y': self.y
        }

    @staticmethod
    def from_db_dict(d):
        return PiecewiseLinFunction(
            x=d['X'],
            y=d['Y'],
            x_unit=d['UnitX'],
            y_unit=d['UnitY'],
            data_id=DataID[d['DataID']],
            value_type=ValueType[d['ValueType']]
        )