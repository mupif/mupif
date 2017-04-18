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
import Pyro4

@Pyro4.expose
class MupifObject(object):
    """
    An abstract class representing a base Mupif object.

    The purpose of this class is to represent any mupif object;
    it introduce basic methods for getting and setting object metatdata.

    .. automethod:: __init__
    """
    def __init__ (self):
        """
        Constructor. Initializes the object
        """
        self.metadata = {}

    def getMetadata (self, key):
        """ 
        Returns metadata associated to given key
        :return: metadata associated to key, throws TypeError if key does not exist
        """
        return self.metadata[key];
    
    def hasMetadata (self, key):
        """ 
        Returns true if key defined
        :return: true if key defined, false otherwise
        :rtype: bool
        """
        return self.metadata.has_key(key)
    
    def setMetadata (self, key, val):
        """ 
        Sets metadata associated to given key
        """
        self.metadata[key] = val
        
