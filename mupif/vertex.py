from builtins import object
from . import bbox
from .baredata import BareData
import Pyro5.api
import typing
from .ndtypes import *


@Pyro5.api.expose
class Vertex(BareData):
    """
    Represent a vertex. Vertices define the geometry of interpolation cells. Vertex is characterized by its position, number and label. Vertex number is locally assigned number, while label is a unique number referring to source application.

    .. automethod:: __init__
    .. automethod:: __repr__
    """
    number: int  #: Local vertex number
    label: typing.Optional[int] = None  #: Vertex label
    coords: NDArr23  #: 3D position vector of a vertex

    # class Config:
    #     frozen=True

    def __hash__(self): return id(self)

    def getCoordinates(self) -> NDArr23:
        """
        :return: Receiver's coordinates
        :rtype: tuple
        """
        return self.coords

    def getNumber(self) -> int:
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
        # print(f'__repr__ on {self.number=}, {self.label=}, {self.coords=}')
        return '['+repr(self.number)+','+repr(self.label)+','+repr(self.coords.tolist())+']'
