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

class Localizer(object):
    """
    A Localizer is an abstract class representing an algorithm used to 
    partition space and quicly localize the contained objects.
    """
    def insert (self, item):
        """
        Inserts given object to Localizer. Object is assume to 
        provide giveBBox() method returning bounding volume if itself.
        """

    def delete (self, item):
        """
        Deletes the given object from Localizer data structure.
        """
    
    def giveItemsInBBox (self, bbox):
        """
        Returns the list of all objects which bbox intersects with given bbox
        """
        return []

    def evaluate(self, functor):
        """
        Returns the list of all objects for which the functor is satisfied.
        The functor is a class with two methods:
        giveBBox() which returns an initial functor bbox 
        evaluate(obj) which should return true if functor is satisfied for given object.
        """
        return []
