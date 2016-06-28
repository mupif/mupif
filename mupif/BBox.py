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

from builtins import zip, str, range, object

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
            self.coords_ll=tuple([min(self.coords_ll[i],entity.coords_ll[i]) for i in range(nsd)])
            self.coords_ur=tuple([max(self.coords_ur[i],entity.coords_ur[i]) for i in range(nsd)])
        else:
            # Merge with given coordinates
            self.coords_ll=tuple([min(self.coords_ll[i],entity[i]) for i in range(nsd)])
            self.coords_ur=tuple([max(self.coords_ur[i],entity[i]) for i in range(nsd)])


try:
    from minieigen import AlignedBox3
    BBoxBase=AlignedBox3
    # add zero 3rd coordinate to 2-tuples
    def extend2d(arg): return (arg[0],arg[1],0) if len(arg)==2 else arg
    # some methods are called different, this adds the API of BBox from above
    BBoxBase.containsPoint=lambda self,p: self.contains(extend2d(p))
    BBoxBase.merge=AlignedBox3.extend
    BBoxBase.coords_ll=property(lambda self: self.min, lambda self,val: setattr(self,'min',extend2d(val)))
    BBoxBase.coords_ur=property(lambda self: self.max, lambda self,val: setattr(self,'max',extend2d(val)))
    BBoxBase.intersects=lambda self,b: not self.intersection(b).empty()
    # this definition hijacks the plain BBox class defined without fastOctant
    # it acts as pseudo-ctor which handles 2d coords by adding the 3rd, and checks for consistency
    def BBox(mn,mx):
        if len(mn)!=len(mx): raise ValueError("Min/max must have the same dimension (not %d/%d)."%(len(mn),len(mx)))
        if len(mn)==2: return BBoxBase((mn[0],mn[1],0),(mx[0],mx[1],0))
        elif len(mn)==3: return BBoxBase(mn,mx)
        else: raise ValueError("Min/max dimension must be 2 or 3 (not %d)."%len(mn))
    print('mupif.fast: using minieigen.AlignedBox3')
except ImportError:
    pass
    # print('mupif.fast: NOT using minieigen.AlignedBox3')
