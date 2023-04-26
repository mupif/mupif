import Pyro5.api
import pickle
import collections
import typing
import pydantic
import numpy as np

from . import dataid
from . import mupifquantity
from . import units
from . import data
from .units import Quantity, Unit, findUnit
from .dbrec import DbDictable


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
        return self.getDataID()

    def getDataID(self):
        """
        Returns DataID of property.
        :rtype: DataID
        """
        return self.propID


@Pyro5.api.expose
class ConstantProperty(Property,DbDictable):
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

    def saveHdf5(self, hdf5):
        import h5py
        h5 = h5py.File(hdf5, 'w')
        h5.attrs['format'] = 'mupif.Property.saveHdf5:1.0'
        ds = h5.create_dataset(self.propID.name, shape=self.quantity.value.shape, dtype=self.quantity.value.dtype)
        ds.attrs['unit'] = str(self.quantity.unit)
        ds.attrs['valueType'] = self.valueType.name
        if self.time is not None:
            ds.attrs['time'] = str(self.time)
        ds[()] = self.quantity.value
        h5.close()

    @staticmethod
    def loadHdf5(hdf5):
        import h5py
        h5 = h5py.File(hdf5, 'r')
        if 'format' not in h5.attrs:
            raise IOError('HDF5 root does not define "format" attribute.')
        fmt = h5.attrs['format']
        if fmt == 'mupif.Property.saveHdf5:1.0':
            if (l := len(h5.keys())) != 1:
                raise IOError(f'{fmt}: HDF5 root must contain exactly one entity (not {l}).')
            loc = list(h5.keys())[0]
            ds = h5[loc]
            ret = ConstantProperty(
                quantity=units.Quantity(value=np.array(ds), unit=ds.attrs['unit']),
                propID=dataid.DataID[loc],
                valueType=mupifquantity.ValueType[ds.attrs['valueType']],
                time=(units.Quantity(ds.attrs['time']) if 'time' in ds.attrs else None)
            )
            h5.close()
            return ret
        else:
            raise IOError(f'Unhandled HDF5 format {fmt} (must be: mupif.Property.saveHdf5:1.0)')

    def inUnitsOf(self, unit):
        """
        Express the quantity in different units.
        """
        return ConstantProperty(quantity=self.quantity.inUnitsOf(unit), propID=self.propID, valueType=self.valueType, time=self.time)

    def to_db_dict_impl(self):
        return {
            'ClassName': 'ConstantProperty',
            'ValueType': self.valueType.name,
            'DataID': self.propID.name,
            'Unit': str(self.quantity.unit),
            'Value': self.quantity.value.tolist(),
            'Time': self.time.inUnitsOf('s').value if self.time is not None else None
        }

    @staticmethod
    def from_db_dict(d):
        t = None
        if d.get('Time', None) is not None:
            t = d.get('Time') * units.U.s
        return ConstantProperty(
            quantity=units.Quantity(value=np.array(d['Value']), unit=d['Unit']),
            propID=dataid.DataID[d['DataID']],
            valueType=mupifquantity.ValueType[d['ValueType']],
            time=t
        )

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
