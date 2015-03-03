class Property(object):
        """
        Property is a characteristic value of a problem, 
        that does not depend on spatial variable.

        Property represents characteristic value  of the problem. 
        It can represent value of scalar, vector, or tensorial type. 
        Property keeps its value, objectID, time and type.

        Attributes:
            value(tuple): A tuple(array) representing property value
            time(double): Time 
            type(int): Determines type of a property
            objectID(int): Determines optional ID of problem object/subdomain
            units: Property units
        """
        def __init__(self, value, propID, valueType, time, units, objectID=0):
            """
            Initializes the property.

            ARGS:
                value(tuple): value of property.
                  Scalar value is represented as array of size 1. 
                  Vector is represented as values packed in tuple.
                  Tensor is represented as 3D tensor stored in tuple, column by column.
		propId(PropertyID): property id
		valueType(ValueType): type of property value 
	        time(double): time 
                units: property units
                objectID(int): optional ID of problem object/subdomain to which 
                  property is related.
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

            Returns:
                Property value as array (tuple); 
            """
            return self.value

        def getPropertID(self):
            """
            Returns type of property.

            RETURNS:
                Receiver property id (PropertyID)
            """
            return self.propID

        def getObjectID(self):
            """
            Returns property objectID.

            RETURNS:
                int
            """
            return self.objectID

        def getUnits(self):
            """
            Returns representation of property units.

            Returns:
            Returns receiver's units (Units)
            """
            return self.units
