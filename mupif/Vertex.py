class Vertex(object):
    """
    Represent vertex.
    Vertices in general define the geometry of interpolation cells.
    Vertex is characterized by its position, number and label.
    Vertex number is locally assigned number, while label is unique number referring
    to source application.
    """
    def __init__(self, number, label, coords=None):
        """
        Initializes the vertex.
        ARGS:
            number(int): local vertex number 
            label(int):  vertex label 
            coords(tuple): 3D position vector of vertex.
        """
        self.number=number
        self.label=label
        self.coords=coords

    def getCoordinates(self):
        """
        Returns the receiver coordinates.
        """
    def __repr__(self):
        return '['+repr(self.number)+','+repr(self.label)+','+repr(self.coords)+']'

