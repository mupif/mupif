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
from .mValType import MValType
from . import mValType
import Pyro4
import json
import pprint
#from dotmap import DotMap



@Pyro4.expose
class MupifObject(object):
    """
    An abstract class representing a base Mupif object.

    The purpose of this class is to represent any mupif object;
    it introduce basic methods for getting and setting object metatdata.

    .. automethod:: __init__
    """
    def __init__(self, jsonFileName=''):
        """
        Constructor. Initializes the object
        :param str jsonFileName: Optionally instantiate from JSON file
        """
        self.metadata = {}
        
        if jsonFileName:
            with open(jsonFileName) as f:
                self.metadata = json.load(f)
        

    def getMetadata(self, key):
        """ 
        Returns metadata associated to given key
        :param key: unique metadataID 
        :return: metadata associated to key, throws TypeError if key does not exist
        :raises: TypeError
        """
        return self.metadata[key]
    
    def hasMetadata(self, key):
        """ 
        Returns true if key defined
        :param key: unique metadataID 
        :return: true if key defined, false otherwise
        :rtype: bool
        """
        return key in self.metadata
    
    def printMetadata(self):
        """ 
        Print all metadata
        :return: None
        :rtype: None
        """
        pprint.pprint(self.metadata, width=300)
    
    def setMetadata (self, key, val):
        """ 
        Sets metadata associated to given key
        :param key: unique metadataID 
        :param val: any type
        
        """
        self.metadata[key]=val
        

    def validateMetadata(self, template):
        """
        TODO
        """
        #metadataFlat = mValType.flattenDict(self.metadata)
        #templateFlat = mValType.flattenDict(template)
        mValType.compare(template, self.metadata, self)
        
        
    def __str__(self):
        """
        Returns printable string representation of an object.
        :return: string
        """
        return str(self.__dict__)

    def toJSON(self, indent=4):
        """
        By default, the JSON encoder only understands native Python data types (str, int, float, bool, list, tuple, and dict). Other classes need 
        JSON serialization method
        :return: string
        """
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=indent)
    
    def toJSONFile(self, filename, indent=4):
        with open(filename,"w") as f:
            json.dump(self.metadata,f, default=lambda o: o.__dict__, sort_keys=True, indent=indent)
    
        
