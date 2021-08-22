from . import mupifobject
import Pyro5.api
import typing
import pydantic


from .units import Quantity


@Pyro5.api.expose
class LookupTable(mupifobject.MupifObject):
    """

    .. automethod:: __init__
    """

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)
        defaults = dict([
            ('Type', 'mupif.lookuptable.LookUpTable'),
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
    default_value: float = None
    tolerance: float = 0.0001

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)

    def setData(self, data):
        if len(data):
            len_check = len(data[0])
            for record in data:
                if len(record) != len_check:
                    raise ValueError("All data must have the same length!")
            self.data = data

    def evaluate(self, params):
        """
        Returns the value for given parameters.

        :rtype: Quantity
        """
        len_record = len(self.data[0])-1
        if len(params) != len_record:
            raise ValueError("Unexpected number of given parameters.")
        for record in self.data:
            match = True
            for j in range(0, len_record):
                if params[j] < record[j+1]-self.tolerance or params[j] > record[j+1]+self.tolerance:
                    match = False
                    break
            if match is True:
                return record[0]
        return self.default_value
