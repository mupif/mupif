from builtins import object
class Property(object):
        """
        Property is a characteristic value of a problem, that does not depend on spatial variable, e.g. homogenized conductivity over the whole domain.

        Property represents characteristic value  of the problem. It can represent value of scalar, vector, or tensorial type. Property keeps its value, objectID, time and type.

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

        def getValue(self):
            """
            Returns the value of property in a tuple.

            :return: Property value as array
            :rtype: tuple
            """
            return self.value

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
