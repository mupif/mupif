class Field:
    """
    Representation of field. Field is a scalar, vector, or tensorial 
    quantity defined on spatial domain. The field, however is assumed
    to be fixed in time. The field can be evaluated in any spatial point 
    belonging to underlying domain. 

    Derived classes will implement fields defined on common discretizations, 
    like fields defined on structured/unstructured FE meshes, FD grids, etc.
    """
    def __init__(self, mesh, fieldID, valueType, units, time, values=None):
        """
        Initializes the field instance.

        ARGS:
            mesh(Mesh): Instance of Mesh class representing underlying discretization.
            fieldID(FieldID): field type
            valueType(ValueType): type of field values 
            units: units of the field values
            time(double): time
            values(tuple): field values (format dependent of particular field type)
        """
    def getMesh(self):
        """
        Returns representation of underlying discretization.
        RETURNS:
            Mesh
        """
        return self.mesh

    def getValueType(self):
        """
        Returns value type (ValueType) of the receiver.
        """
        return self.value_type

    def getFieldID(self):
        """
        Returns field ID (FieldID type).
        """
        return self.field_id

    def evaluate(self, position, eps=0.001):
        """
        Evaluates the receiver at given spatial position.

        ARGS:
            position (tuple): 3D position vector
            eps(double): Optional tolerance
        RETURNS:
            tuple. 
        """
    def giveValue(self, componentID):
        """
        Returns the value associated to given component (vertex or cell IP).
        ARGS:
            componentID(tuple): identifies the component (vertexID,) or (CellID, IPID)
        """
    def setValue(self, componentID, value):
        """
        Sets the value associated to given component (vertex or cell IP).
        ARGS:
            componentID(tuple):  The componentID is a tuple: (vertexID,) or (CellID, IPID)
            value(tuple):        Value to be set for given component
        NOTE:
            If mesh has mapping attached (a mesh view) then we have to remember value 
            locally and record change.
            The source field values are updated after commit() method is invoked.
        """
    def commit(self):
        """
        Commits the recorded changes (via setValue method) to primary field.
        """
    def getUnits(self):
        """
        Returns units of the receiver.
        """
    def merge(self, field):
        """
        Merges the receiver with given field together. 
        Both fields should be on different parts of the domain (can also overlap),
        but should refer to same underlying discretization, 
        otherwise unpredictable results can occur.
        """
    def field2VTKData (self):
        """
        Returns VTK representation of the receiver. Useful for visualization.
        RETURNS:
            VTKDataSource
        """
