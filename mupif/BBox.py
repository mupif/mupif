from builtins import zip, str, range, object
# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
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

debug = 0

class BBox(object):
    """
    Represents a bounding box - a rectange in 2D and prism in 3D.
    Its geometry is described using two points - lover left and upper right corners.
    The bounding box class provides fast and efficient methods for testing whether
    point is inside it and whether intersection with other BBox exist.
    
    .. automethod:: __init__
    .. automethod:: __str__
    """
    def __init__(self, coords_ll, coords_ur):
        """
        Constructor.

        :param tuple coords_ll: Tuple with coordinates of lower left corner
        :param tuple coords_ur: Tuple with coordinates of uper right corner
        """
        self.coords_ll = coords_ll
        self.coords_ur = coords_ur
        
    def __str__ (self):
        """
        :return: Returns lower left and upper right coordinate of the bounding box
        :rtype: str
        """
        return "BBox ["+str(self.coords_ll)+"-"+str(self.coords_ur)+"]"

    def containsPoint (self, point):
        """
        Check whether a point lies within a receiver.
        
        :param tuple point: 1D/2D/3D position vector
        :return: Returns True if point is inside receiver, otherwise False
        :rtype: bool
        """
        for l, u, x in zip (self.coords_ll, self.coords_ur, point):
            if (x<l or x>u):
                return False
        return True

    def intersects (self, bbox):
        """ 
        Check intersection of a receiver with a bounding box
        
        :param BBox bbox: an instance of BBox class
        :return: Returns True if receiver intersects given bounding box, otherwise False
        :rtype: bool
        """
        nsd = len(self.coords_ll)
        for i in range(nsd):
            maxleft = max(self.coords_ll[i], bbox.coords_ll[i])
            minright= min(self.coords_ur[i], bbox.coords_ur[i])
            if maxleft > minright: 
                return False
        return True

    def merge (self, entity):
        """
        Merges receiver with given entity (position vector or a BBox).
        
        :param tuple entity: 1D/2D/3D position vector or
        :param BBox entity: an instance of BBox class
        """
        nsd = len(self.coords_ll)
        if isinstance(entity, BBox):
            # Merge with given bbox
            for i in range(nsd):
                self.coords_ll[i]=min(self.coords_ll[i], entity.coords_ll[i])
                self.coords_ur[i]=max(self.coords_ur[i], entity.coords_ur[i])
        else:
            # Merge with given coordinates
            for i in range(nsd):
                self.coords_ll[i]=min(self.coords_ll[i], entity[i])
                self.coords_ur[i]=max(self.coords_ur[i], entity[i])


try:
    from minieigen import AlignedBox3
    BBox=AlignedBox3
    BBox.containsPoint=AlignedBox3.contains
    BBox.merge=AlignedBox3.extend
    BBox.coords_ll=property(lambda self: self.min, lambda self,val: setattr(self,'min',val))
    BBox.coords_ur=property(lambda self: self.max, lambda self,val: setattr(self,'max',val))
    BBox.intersects=lambda self,b: not self.intersection(b).empty()
    print('mupif.fast: using minieigen.AlignedBox3')
except ImportError:
    pass
    # print('mupif.fast: NOT using minieigen.AlignedBox3')
