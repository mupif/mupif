class Cell:
    """
    Representation of computational cell. 
    
    The solution domain is composed of cells, whose geometry is defined using vertices.
    Cells provide interpolation over their associated volume, based on given vertex values.
    Derived classes will be implemented to support common interpolation cells 
    (finite elements, FD stencils, etc.)
    """
    def __init__(self, mesh, number, label, vertices):
        """
        Initialize the cell.

        ARGS:
            mesh(Mesh): the mesh to which cell belongs.
            number(int): local cell number
            label(int):  cell label
            vertices(tuple): cell vertices (local numbers)
        """
    def copy(self):
        """
        This will copy the receiver, making deep copy of all 
        attributes EXCEPT mesh attribute
        Returns:
            the copy of receiver (Cell)
        """
        return self.__class__(self.mesh, self.number, self.label, tuple(self.vertices))

    def getVertices (self):
        """
        Returns:
           the list of cell vertices (tuple of Vertex instances)
        """
        if all(isinstance(v,int) for v in self.vertices):
            return [self.mesh.giveVertex(i) for i in self.vertices]
        return self.vertices

    def containsPoint (self, point):
        """Returns true if cell contains given point"""
    
    def interpolate (self, point, vertexValues):
        """
        Interpolates given vertex values to given point)
        ARGS:
           point(tuple) position vector
           vertexValues(tuple) A tuple containing vertex values 
        Returns:
           interpolated value (tuple) at given point
        """
    
    def getGeometryType(self):
        """
        Returns geometry type of receiver (CellGeometryType)
        """

    def getBBox(self):
        """ 
        Returns bounding box of the receiver (BBox)
        """
