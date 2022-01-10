from . import mupifobject
import Pyro5.api
import typing
import pydantic
import numpy as np

from .units import Quantity
from .units import Unit
from .dataid import DataID
from .property import ConstantProperty
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
        if data_id in self.y_data_ids:
            idx = None
            i = 0
            for did in self.y_data_ids:
                if did == data_id:
                    idx = i
                    break
                i += 1

            if idx is not None:
                x_float = x.inUnitsOf(self.x_unit).value
                value_data = []
                for i in range(0, len(self.y[idx][0])):
                    ydata = [a[i] for a in self.y[idx]]
                    value_data.append(np.interp(x=x_float, xp=self.x, fp=ydata))
                return ConstantProperty(value=value_data, propID=self.y_data_ids[idx], valueType=self.y_value_types[idx], unit=self.y_units[idx])

        else:
            raise ValueError("DataID %s not found in Y data." % str(data_id))
