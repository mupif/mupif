from builtins import object
import Pyro4
try:
   import cPickle as pickle #faster serialization if available
except:
   import pickle

@Pyro4.expose
class Property(object):
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
            :param ValueType valueType: Type of a property, i.e. scalar, vector, tensor
            :param float time: Time
            :param PhysicalQuantity units: Property units
            :param int objectID: Optional ID of problem object/subdomain to which property is related, default = 0
            """
            self.value = value
            self.propID = propID
            self.time = time
            self.units = units
            self.valueType = valueType
            self.objectID = objectID

        @classmethod
        def loadFromLocalFile(cls,fileName):
            """
            Alternative constructor from a Pickle module

            :param str fileName: File name

            :return: Returns Property instance
            :rtype: Property
            """
            return pickle.load(open(fileName,'rb'))

        def getValue(self):
            """
            Returns the value of property in a tuple.

            :return: Property value as array
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
            :rtype: float
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
            return self.units

        def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
            """
            Dump Property to a file using Pickle module

            :param str fileName: File name
            :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
            """
            pickle.dump(self, open(fileName,'wb'), protocol)

