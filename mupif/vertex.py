from builtins import object
from . import bbox
from .dumpable import Dumpable
import Pyro5
from pydantic.dataclasses import dataclass
import typing


@Pyro5.api.expose
class Vertex(Dumpable):
    """
    Represent a vertex. Vertices define the geometry of interpolation cells. Vertex is characterized by its position, number and label. Vertex number is locally assigned number, while label is a unique number referring to source application.

    .. automethod:: __init__
    .. automethod:: __repr__
    """
    number: int  #: Local vertex number
    label: typing.Optional[int]  #: Vertex label
    coords: typing.Union[typing.Tuple[float, float], typing.Tuple[float, float, float]]  #: 3D position vector of a vertex

    # class Config:
    #     frozen=True

    def __hash__(self): return id(self)

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
