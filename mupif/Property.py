from . import MupifObject
from mupif.Physics import PhysicalQuantities
from mupif .Physics.PhysicalQuantities import PhysicalQuantity
import Pyro4
try:
   import cPickle as pickle #faster serialization if available
except:
   import pickle

@Pyro4.expose
class Property(MupifObject.MupifObject, PhysicalQuantity):
        """
        Property is a characteristic value of a problem, that does not depend on spatial variable, e.g. homogenized conductivity over the whole domain. Typically, properties are obtained by postprocessing results from lover scales by means of homogenization and are parameters of models at higher scales.

        Property value can be of scalar, vector, or tensorial type. Property keeps its value, objectID, time and type.

        .. automethod:: __init__
        """
        def __init__(self, value, propID, valueType, time, units, objectID=0):
            """
            Initializes the property.

            :param tuple value: A tuple (array) representing property value
            :param PropertyID propID: Property ID
            :param ValueType valueType: Type of a property, i.e. scalar, vector, tensor. Tensor is by default a tuple of 9 values, being compatible with Field's tensor.
            :param Physics.PhysicalQuantity time: Time
            :param units: Property units or string
            :type units: Physics.PhysicalUnits or string
            :param int objectID: Optional ID of problem object/subdomain to which property is related, default = 0
            """
            super(Property, self).__init__()
            self.value = value
            self.propID = propID
            self.time = time
            #self.units = units
            self.valueType = valueType
            self.objectID = objectID

            if (PhysicalQuantities.isPhysicalUnit(units)):
               self.unit = units
            else:
               self.unit = PhysicalQuantities._findUnit(units)

        @classmethod
        def loadFromLocalFile(cls,fileName):
            """
            Alternative constructor from a Pickle module

            :param str fileName: File name

            :return: Returns Property instance
            :rtype: Property
            """
            return pickle.load(open(fileName,'rb'))

        def __str__(self):
            return str(self.value) + '{' + self.unit.name() + ',' + str(self.propID) + ',' + str(self.valueType) + '}'

        def __repr__(self):
            return (self.__class__.__name__ + '(' +
                    repr(self.value) + ',' +
                    repr(self.unit.name()) +',' +
                    repr(self.propID)+',' +
                    repr(self.valueType) + ')')

        def getValue(self, time=None):
            """
            Returns the value of property in a tuple.
            :param Physics.PhysicalQuantity time: Time of property evaluation

            :return: Property value as an array
            :rtype: tuple
            """
            return self.value

        def getValueType(self):
            """
            Returns the value type of property.

            :return: Property value type
            :rtype: mupif.PropertyID
            """
            return self.valueType

        def getTime(self):
            """
            Returns time associated with this property.

            :return: Time
            :rtype: Physics.PhysicalQuantity
            """
            return self.time

        def getPropertyID(self):
            """
            Returns type of property.

            :return: Receiver's property ID
            :rtype: PropertyID
            """
            return self.propID

        def getObjectID(self):
            """
            Returns property objectID.

            :return: Object's ID 
            :rtype: int
            """
            return self.objectID

        def getUnits(self):
            """
            Returns representation of property units.

            :return: Returns receiver's units (Units)
            :rtype: PhysicalQuantity
            """
            return self.unit

        def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
            """
            Dump Property to a file using Pickle module

            :param str fileName: File name
            :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
            """
            pickle.dump(self, open(fileName,'wb'), protocol)
        def _sum(self, other, sign1, sign2):
            """
            Override of PhysicalQuantity._sum method
            """
            if not PhysicalQuantities.isPhysicalQuantity(other):
               raise TypeError('Incompatible types')
            factor = other.unit.conversionFactorTo(self.unit)
            new_value = tuple(sign1*s+sign2*o*factor for (s,o) in zip(self.value, other.value))
            #new_value = sign1*self.value + \
            #            sign2*other.value*other.unit.conversionFactorTo(self.unit)
            return self.__class__(new_value, self.propID, self.valueType, self.time, self.unit)

        def _convertValue (self, value, src_unit, target_unit):
           """
           Helper function to evaluate value+offset*factor, where
           factor and offset are obtained from 
           conversionTupleTo(target_unit)
           """
           (factor, offset) = src_unit.conversionTupleTo(target_unit)
           return tuple((v+offset)*factor for v in value)
        
        def convertToUnit(self, unit):
           """
           Change the unit and adjust the value such that
           the combination is equivalent to the original one. The new unit
           must be compatible with the previous unit of the object.
           
           :param C{str} unit: a unit
         
           :raise TypeError: if the unit string is not a know unit or a unit incompatible with the current one
           """
           unit = PhysicalQuantities._findUnit(unit)
           self.value = self._convertValue (self.value, self.unit, unit)
           self.unit = unit
        def inUnitsOf(self, *units):
           """
           Express the quantity in different units. If one unit is
           specified, a new PhysicalQuantity object is returned that
           expresses the quantity in that unit. If several units
           are specified, the return value is a tuple of
           PhysicalObject instances with with one element per unit such
           that the sum of all quantities in the tuple equals the
           original quantity and all the values except for the last one
           are integers. This is used to convert to irregular unit
           systems like hour/minute/second.
           
           :param units: one units
           :type units: C{str} 
           
           :returns: one physical quantity
           :rtype: L{PhysicalQuantity} or C{tuple} of L{PhysicalQuantity}
           :raises TypeError: if any of the specified units are not compatible with the original unit
           """
           units = list(map(PhysicalQuantities._findUnit, units))
           unit = units[0]
           value = self._convertValue (self.value, self.unit, unit)
           return self.__class__(value, self.propID, self.valueType, self.time, unit)
