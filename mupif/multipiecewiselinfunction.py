from . import mupifobject
import Pyro5.api
import typing
import pydantic
import numpy as np

from .units import Quantity
from .units import Unit
from .dataid import DataID
from .property import Property, ConstantProperty
from .mupifquantity import ValueType


@Pyro5.api.expose
class MultiPiecewiseLinFunction(mupifobject.MupifObject):
    """

    .. automethod:: __init__
    """

    x: typing.List[float] = []
    x_unit: Unit = None
    y: typing.List[typing.List[float]] = []
    y_units: typing.List[Unit] = []
    y_data_ids: typing.List[DataID] = []
    y_value_types: typing.List[ValueType] = []

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)
        defaults = dict([
            ('Type', 'mupif.MultiPiecewiseLinFunction'),
        ])
        for k, v in defaults.items():
            if k not in metadata:
                self.updateMetadata(dict(k=v))

    def setXData(self, data, unit):
        if len(self.y) == 0 or len(self.x) == len(data):
            self.x = data
            self.x_unit = unit
        else:
            raise SyntaxError("Size of X axis cannot be changed after adding Y data.")

    def addYData(self, data, unit, data_id, value_type):
        if len(self.x) == 0 or self.x_unit is None:
            raise SyntaxError("X axis must be defined before adding Y axis values")
        elif data_id in self.y_data_ids:
            raise ValueError("DataID value can be used only once.")
        elif len(self.x) != len(data):
            raise ValueError("Y data must have equal size as the X data.")
        else:
            self.y.append(data)
            self.y_units.append(unit)
            self.y_data_ids.append(data_id)
            self.y_value_types.append(value_type)

    def evaluate(self, x, data_id):
        if data_id not in self.y_data_ids: raise KeyError(f"DataID {data_id} not found in Y data.")
        idx = self.y_data_ids.index(data_id)
        x_float = x.inUnitsOf(self.x_unit).value
        value_data = []
        for i in range(len(self.y[idx][0])):
            ydata = [a[i] for a in self.y[idx]]
            value_data.append(np.interp(x=x_float, xp=self.x, fp=ydata))
        return ConstantProperty(value=value_data, propID=self.y_data_ids[idx], valueType=self.y_value_types[idx], unit=self.y_units[idx])


@Pyro5.api.expose
class MultiPiecewiseLinFunction2(mupifobject.MupifObject):

    x: Quantity
    yy: typing.List[ConstantProperty] = pydantic.Field(default_factory=lambda: [])

    def __init__(self, **kw):
        super().__init__(**kw)
        self._check_x(self.x.value)

    def _check_x(self, x):
        if not (x.ndim == 1 and x.size > 1 and np.all(np.diff(x) > 0)):
            raise ValueError('x array must be 1D, with at least 2 elements and be strictly increasing.')

    # x normally set in the ctor
    # def setX(self, x: Quantity):
    #     self._check_x(x.value)
    #     if self.y and len(self.y[0]) != len(x):
    #         raise ValueError('X must have the same length as y (len(x)={len(x)}, len(y)={len(self.y)})')
    #     self.x = x

    def addY(self, y: Property):
        if y.getPropertyID() in set([p.getPropertyID() for p in self.yy]):
            raise ValueError(f'Property ID {y.getPropertyID()} already defined.')
        self.yy.append(y)

    def evaluate(self, x: Quantity, data_id):
        assert self.x.value.size > 1
        if len(y_ := [y for y in self.yy if y.getPropertyID() == data_id]) != 1:
            raise KeyError(f'No data with id {data_id}.')
        y = y_[0]
        if x < self.x[0] or x > self.x[-1]:
            raise ValueError(f'x={x} not in range {self.x[0]}..{self.x[1]}')
        return Property(quantity=np.interp(x=x, xp=self.x, fp=y.quantity, left=np.nan, right=np.nan), propID=data_id, valueType=y.valueType)
