class Mesh:
    """
    Abstract representation of a computational domain.
    Described using computational cells and vertices, determining the cell geometry.
    Derived classes represent structured, unstructured FE grids, FV grids, etc.

    Mesh is assumed to provide a suitable instance of cell and vertex localizers.
    """
    def __init__(self):
        self.mapping = None

    def copy(self):
        """
        This will return a copy of the receiver. 
        NOTE: 
            DeepCopy will not work, as individual cells contain mesh link attributes, 
            leading to underlying mesh duplication in every cell!
        Returns:
            Copy of receiver (Mesh)
        """
    def getNumberOfVertices(self):
        """Returns the number of Vertices."""
        return 0;

    def getNumberOfCells(self):
        """Returns the number of Cells."""
        return 0;
        
    def getVertex(self, i):
        """
        Returns i-th vertex.
        Returns:
             vertex (Vertex)
        """

    def getCell(self, i):
        """
        Returns i-th cell.
        Returns:
             cell (Cell)
        """
        
    def getMapping(self):
        """Returns the mapping associated to mesh."""
        return self.mapping

    def vertexLabel2Number(self, label):
        """
        Returns local vertex number corresponding to given label.
        If no label corresponds, throws an exception
        Returns:
           vertex number (int)
        """
        
    def cellLabel2Number(self, label):
        """
        Returns local cell number corresponding to given label.
        If no label corresponds, throws an exception
        
        Returns:
            cell number (int)
        """
