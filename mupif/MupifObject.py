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
    def __init__ (self):
        """
        Constructor. Initializes the object
        """
        self.metadata = {}

    def getMetadata (self, key):
        """ 
        Returns metadata associated to given key
        :param key: unique metadataID 
        :return: metadata associated to key, throws TypeError if key does not exist
        :raises: TypeError
        """
        return self.metadata[key];
    
    def hasMetadata (self, key):
        """ 
        Returns true if key defined
        :param key: unique metadataID 
        :return: true if key defined, false otherwise
        :rtype: bool
        """
        return (key in self.metadata)
    
    def printMetadata(self):
        """ 
        Print all metadata
        :return: None
        :rtype: None
        """
        pprint.pprint(self.metadata,width=300)
    
    
    def createNestedDict(self, data, val):
        if len(data) == 0:
            return data #trivial case, we have no element therefore we return empty list
        else: #if we have elements
            first_value = data[0] #we take the first value
            return {first_value : val} if len(data)==1 else {first_value : self.createNestedDict(data[1:],val)}
    
    
    
    def setMetadata (self, key, val):
        """ 
        Sets metadata associated to given key
        :param key: unique metadataID 
        :param val: any type
        
        TODO-dot
        """
        #dm = DotMap(self.metadata)
        #dm[key] = val
        #We can not use aa.bb as a single key since it could be nested dictionary
        #keys = key.split('.')
        #d=self.createNestedDict(keys,val)
        
        self.metadata[key]=val
        
        #print(self.metadata)
        #aa={'Model': 1, 'b': 3, 'c': 4}
        #self.metadata.update(aa)
        #print(self.metadata)
        
        #print(type(self.metadata))
        #print(self.metadata)
        
        
        
    def validateMetadata(self, template):
        """
        TODO
        """
        #metadataFlat = mValType.flattenDict(self.metadata)
        #templateFlat = mValType.flattenDict(template)
        mValType.compare(template, self.metadata)
        
        
    def __str__(self):
        """
        Returns printable string representation of an object.
        :retrun: string
        """
        return str(self.__dict__)

    def toJSON(self):
        """
        JSON serialization method
        :return: string
        """
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
    
    
#@Pyro4.expose
#class mDict:
    #def __init__(self, type, compulsory):
        #self.valType = type
        #self.compulsory = compulsory
    #def __repr__(self): #hide details when printing a dictionary
        #return (self.valType.__name__)

