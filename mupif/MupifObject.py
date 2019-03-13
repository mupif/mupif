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
import json
import jsonschema
import pprint


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
    
    def printMetadata(self, nonEmpty=False):
        """ 
        Print all metadata
        :param bool nonEmpty: Optionally print only non-empty values
        :return: None
        :rtype: None
        """
        print('ClassName:\'%s\'' % self.__class__.__name__)
        if nonEmpty:
            d = {}
            for k, v in self.metadata.items():
                if v != '':
                    d[k] = v
        pprint.pprint(d if nonEmpty else self.metadata, indent=4, width=300)

    def setMetadata(self, key, val):
        """ 
        Sets metadata associated to given key
        :param str key: unique metadataID
        :param val: any type
        """
        keys = key.split('.')
        elem = self.metadata
        i = 0
        i_last = len(keys)-1
        for keyword in keys:
            if i == i_last:
                last = True
            else:
                last = False

            if not last:
                if keyword in elem:
                    elem = elem[keyword]
                else:
                    elem[keyword] = {}
                    elem = elem[keyword]
            else:
                elem[keyword] = val
            i += 1

    def _iterInDictOfMetadataForUpdate(self, dictionary, base_key):
        for key, value in dictionary.items():
            if base_key != "":
                new_key = "%s.%s" % (base_key, key)
            else:
                new_key = "%s" % key

            if isinstance(value, dict):
                self._iterInDictOfMetadataForUpdate(value, new_key)
            else:
                self.setMetadata(new_key, value)
        
    def updateMetadata(self, dictionary):
        """ 
        Updates metadata's dictionary with a given dictionary
        :param dict dictionary: Dictionary of metadata
        """
        if isinstance(dictionary, dict):
            self._iterInDictOfMetadataForUpdate(dictionary, "")

        # self.metadata.update(dictionary)

    def validateMetadata(self, template):
        """
        Validates metadata's dictionary with a given dictionary
        :param dict template: Schema for json template
        """
        jsonschema.validate(self.metadata, template)
        
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
        return json.dumps(self.metadata, default=lambda o: o.__dict__, sort_keys=True, indent=indent)
    
    def toJSONFile(self, filename, indent=4):
        with open(filename, "w") as f:
            json.dump(self.metadata, f, default=lambda o: o.__dict__, sort_keys=True, indent=indent)
