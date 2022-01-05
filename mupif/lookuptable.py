from . import mupifobject
import Pyro5.api
import typing
import pydantic

from .units import Quantity
from .units import Unit


@Pyro5.api.expose
class LookupTable(mupifobject.MupifObject):
    """

    .. automethod:: __init__
    """

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)
        defaults = dict([
            ('Type', 'mupif.LookUpTable'),
        ])
        for k, v in defaults.items():
            if k not in metadata:
                self.updateMetadata(dict(k=v))

    def evaluate(self, params):
        """
        Returns the value for given parameters.

        :rtype: Quantity
        """


@Pyro5.api.expose
class MemoryLookupTable(LookupTable):
    """

    .. automethod:: __init__
    """

    data: typing.List[typing.List[float]] = []  # first column stores the values, the rest of the columns is used to store the parameters
    units: typing.List[Unit] = []  # first element stores unit of the value, the rest of the elements stores units of the particular parameters
    default_value: float = None
    tolerance: float = 0.0001

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)

        self.n_records = len(self.data)
        self.n_params = len(self.data[0])-1

    def _setData(self, data):
        if len(data):
            len_check = len(data[0])
            for record in data:
                if len(record) != len_check:
                    raise ValueError("All data must have the same length!")
            self.data = data

    def evaluate(self, params):
        """
        Returns the value for given parameters.
        :param: Quantity[] params:
        :rtype: Quantity
        """
        if len(params) != self.n_params:
            raise ValueError("Unexpected number of given parameters.")
        for record in self.data:
            match = True
            for j in range(0, self.n_params):
                if params[j].inUnitsOf(self.units[j+1]).value < record[j+1]-self.tolerance or params[j].inUnitsOf(self.units[j+1]).value > record[j+1]+self.tolerance:
                    match = False
                    break
            if match is True:
                return Quantity(record[0], self.units[0])
        return self.default_value
