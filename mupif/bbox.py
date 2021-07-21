# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

from __future__ import annotations

import Pyro5.api
from pydantic.dataclasses import dataclass
from typing import Union, Tuple
from . import dumpable
import pydantic


@Pyro5.api.expose
class BBox(pydantic.BaseModel):
    """
    Represents a bounding box - a rectange in 2D and prism in 3D.
    Its geometry is described using two points - lover left and upper right corners.
    The bounding box class provides fast and efficient methods for testing whether
    point is inside it and whether intersection with other BBox exist.
    
    .. automethod:: __init__
    .. automethod:: __str__
    """
    coords_ll: Union[Tuple[float, float], Tuple[float, float, float]]
    coords_ur: Union[Tuple[float, float], Tuple[float, float, float]]

    def __hash__(self): return id(self)

    # proxy ctor to allow positional arguments
    def __init__(self, coords_ll, coords_ur):
        """
        Constructor.

        :param tuple coords_ll: Tuple with coordinates of lower left corner
        :param tuple coords_ur: Tuple with coordinates of uper right corner
        """
        super().__init__(coords_ll=coords_ll, coords_ur=coords_ur)
        
    def __str__(self):
        """
        :return: Returns lower left and upper right coordinate of the bounding box
        :rtype: str
        """
        return "BBox ["+str(self.coords_ll)+"-"+str(self.coords_ur)+"]"

    def containsPoint(self, point):
        """
        Check whether a point lies within a receiver.
        
        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if point is inside receiver, otherwise False
        :rtype: bool
        """
        for l, u, x in zip(self.coords_ll, self.coords_ur, point):
            if x < l or x > u:
                return False
        return True

    def intersects(self, bbox: BBox):
        """ 
        Check intersection of a receiver with a bounding box
        
        :param BBox bbox: an instance of BBox class
        :return: Returns True if receiver intersects given bounding box, otherwise False
        :rtype: bool
        """
        nsd = len(self.coords_ll)
        mnA, mxA, mnB, mxB = self.coords_ll, self.coords_ur, bbox.coords_ll, bbox.coords_ur
        if nsd == 3:
            return (
                mnA[0] <= mxB[0] and mnA[1] <= mxB[1] and mnA[2] <= mxB[2] and
                mnB[0] <= mxA[0] and mnB[1] <= mxA[1] and mnB[2] <= mxA[2]
            )
        elif nsd == 2:
            return (
                mnA[0] <= mxB[0] and mnA[1] <= mxB[1] and
                mnB[0] <= mxA[0] and mnB[1] <= mxA[1]
            )
        else:
            raise ValueError(f'BBox dimension must be 2 or 3 (not {nsd}).')

        if 0:
            nsd = len(self.coords_ll)
            for i in range(nsd):
                maxleft = max(self.coords_ll[i], bbox.coords_ll[i])
                minright = min(self.coords_ur[i], bbox.coords_ur[i])
                if maxleft > minright: 
                    return False
            return True

    def merge(self, entity):
        """
        Merges receiver with given entity (position vector or a BBox).
        
        :param tuple entity: 1D/2D/3D position vector or
        :param BBox entity: an instance of BBox class
        """
        nsd = len(self.coords_ll)
        if isinstance(entity, BBox):
            # Merge with given bbox
            self.coords_ll = tuple([min(self.coords_ll[i], entity.coords_ll[i]) for i in range(nsd)])
            self.coords_ur = tuple([max(self.coords_ur[i], entity.coords_ur[i]) for i in range(nsd)])
        else:
            # Merge with given coordinates
            self.coords_ll = tuple([min(self.coords_ll[i], entity[i]) for i in range(nsd)])
            self.coords_ur = tuple([max(self.coords_ur[i], entity[i]) for i in range(nsd)])
