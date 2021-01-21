from builtins import object
from . import bbox
import Pyro5


@Pyro5.api.expose
class Vertex(object):
    """
    Represent a vertex. Vertices define the geometry of interpolation cells. Vertex is characterized by its position, number and label. Vertex number is locally assigned number, while label is a unique number referring to source application.

    .. automethod:: __init__
    .. automethod:: __repr__
    """
    def __init__(self, number, label, coords=None):
        """
        Initializes the vertex.

        :param int number: Local vertex number
        :param int label: Vertex label
        :param tuple coords: 3D position vector of a vertex
        """
        self.number = number
        self.label = label
        self.coords = coords

    def getCoordinates(self):
        """
        :return: Receiver's coordinates
        :rtype: tuple
        """
        return self.coords

    def getNumber(self):
        """
        :return: Number of the instance
        :rtype: int
        """
        return self.number

    def getBBox(self):
        """
        :return: Receiver's bounding-box (containing only one point)
        :rtype: mupif.bbox.BBox
        """
        return bbox.BBox(self.coords, self.coords)

    def __repr__(self):
        """
        :return: Receiver's number, label, coordinates
        :rtype: string
        """
        return '['+repr(self.number)+','+repr(self.label)+','+repr(self.coords)+']'
