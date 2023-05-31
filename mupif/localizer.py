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
from builtins import object
import Pyro5.api


@Pyro5.api.expose
class Localizer(object):
    """
    A Localizer is an abstract class representing an algorithm used to partition space and quicly localize the contained objects.
    """
    def insert(self, item):
        """
        Inserts given object to Localizer. Object is assume to provide giveBBox() method returning bounding volume if itself.

        :param object item: Inserted object
        """

    def delete(self, item):
        """
        Deletes the given object from Localizer data structure.

        :param object item: Object to be removed
        """

    def getItemsInBBox(self, bbox):
        """
        :param BBox bbox: Bounding box

        :return: List of all objects which bbox contains and intersects
        :rtype: tuple
        """
        return []

    def evaluate(self, functor):
        """
        Returns the list of all objects for which the functor is satisfied.
 
        :param object functor: The functor is a class which defines two methods: giveBBox() which returns an initial functor bbox and evaluate(obj) which should return True if the functor is satisfied for a given object.

        :return: List of all objects
        :rtype: tuple
        """
        return []
