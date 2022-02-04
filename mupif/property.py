from . import mupifobject
import Pyro5.api
import pickle
import collections
import typing
import pydantic

from . import dataid
from . import mupifquantity
from . import units
from .units import Quantity, Unit, findUnit


@Pyro5.api.expose
class Property(mupifquantity.MupifQuantity):
    """
    Property is a characteristic value of a problem, that does not depend on spatial variable, e.g. homogenized conductivity over the whole domain. Typically, properties are obtained by postprocessing results from lover scales by means of homogenization and are parameters of models at higher scales.

    Property value can be of scalar, vector, or tensorial type. Property keeps its value, time and type.

    .. automethod:: __init__
    """

    propID: dataid.DataID

    def __init__(self, *, metadata={}, **kw):
        super().__init__(metadata=metadata, **kw)
        defaults = dict([
            ('Type', 'mupif.property.Property'),
            ('Type_ID', str(self.propID)),
            ('Units', self.getUnit().to_string()),
            ('ValueType', str(self.valueType))
        ])
        for k, v in defaults.items():
            if k not in metadata:
                self.updateMetadata(dict(k=v))

    def getPropertyID(self):
        """
        Returns type of property.

        :return: Receiver's property ID
        :rtype: DataID
        """
        return self.propID


@Pyro5.api.expose
class ConstantProperty(Property):
    """
    Property is a characteristic value of a problem, that does not depend on spatial variable, e.g. homogenized conductivity over the whole domain. Typically, properties are obtained by postprocessing results from lover scales by means of homogenization and are parameters of models at higher scales.

    Property value can be of scalar, vector, or tensorial type. Property keeps its value, time and type.

    .. automethod:: __init__
    """

    time: typing.Optional[Quantity]

    def __str__(self):
        return str(self.quantity) + '{' + str(self.propID) + ',' + str(self.valueType) + '}@' + str(self.time)

    def __repr__(self):
        return (self.__class__.__name__ + '(' +
                repr(self.quantity) + ',' +
                repr(self.propID)+',' +
                repr(self.valueType) + ',' +
                't=' + repr(self.time) +
                ')')

    def getQuantity(self, time=None):
        if self._timeIsValid(time):
            return self.quantity
        raise ValueError(f'Time out of range (time requested {time}; Property propID {self.propID}, defined at time {self.time})')

    def getValue(self, time=None):
        """
        Returns the value of property in a tuple.
        :param units.Quantity time: Time of property evaluation

        :return: Property value as an array
        :rtype: float or tuple
        """
        if self._timeIsValid(time):
            return self.value
        raise ValueError(f'Time out of range (time requested {time}; Property propID {self.propID}, defined at time {self.time})')

    def _timeIsValid(self, time=None):
        return (self.time is None) or (time is None) or (self.time == time)

    def getTime(self):
        """
        :return: Receiver time
        :rtype: units.Quantity or None
        """
        return self.time

    def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
        """
        Dump Property to a file using Pickle module

        :param str fileName: File name
        :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
        """
        file = open(fileName, 'wb')
        pickle.dump(self, file, protocol)
        file.close()

    @classmethod
    def loadFromLocalFile(cls, fileName):
        """
        Alternative constructor from a Pickle module

        :param str fileName: File name

        :return: Returns Property instance
        :rtype: Property
        """
        file = open(fileName, 'rb')
        ans = pickle.load(file)
        file.close()
        return ans

    def inUnitsOf(self, unit):
        """
        Express the quantity in different units.
        """
        return ConstantProperty(quantity=self.quantity.inUnitsOf(unit), propID=self.propID, valueType=self.valueType, time=self.time)

    # def _convertValue(self, value, src_unit, target_unit):
    #    """
    #    Helper function to evaluate value+offset*factor, where
    #    factor and offset are obtained from
    #    conversionTupleTo(target_unit)
    #    """
    #    (factor, offset) = src_unit.conversionTupleTo(target_unit)
    #    if value.hasVectorValue(): # isinstance(value, collections.Iterable):
    #        return tuple((v+offset)*factor for v in value)
    #    else:
    #        return (value + offset) * factor
