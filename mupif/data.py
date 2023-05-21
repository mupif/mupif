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

import Pyro5.api
import json
import jsonschema
import pprint
import copy
import typing
from .baredata import BareData, ObjectBase
from typing import Optional

import pydantic


@Pyro5.api.expose
class WithMetadata(ObjectBase):
    """
    Class representing a base Mupif object, with metadata.
    """

    metadata: dict = pydantic.Field(default_factory=dict)

    def getMetadata(self, key, default=None):
        """
        Returns metadata associated to given key
        :param key: unique metadataID
        :param default: default value returned when key is not found (otherwise KeyError is thrown)
        :return: metadata associated to key, throws TypeError if key does not exist
        """
        keys = key.split('.')
        d = copy.deepcopy(self.metadata)
        while True:
            try:
                d = d[keys[0]]
            except KeyError:
                if default is not None:
                    return default
                raise
            if len(keys) == 1:
                return d
            keys = keys[1:]

    def getAllMetadata(self):
        """
        :rtype: dict
        """
        return copy.deepcopy(self.metadata)
    
    def hasMetadata(self, key):
        """
        Returns true if key defined
        :param key: unique metadataID
        :return: true if key defined, false otherwise
        :rtype: bool
        """
        keys = key.split('.')
        elem = self.getAllMetadata()
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
                return keyword in elem
            i += 1

        return False
    
    def printMetadata(self, nonEmpty=False):
        """ 
        Print all metadata
        :param bool nonEmpty: Optionally print only non-empty values
        :return: None
        :rtype: None
        """
        print('ClassName:\'%s\'' % self.__class__.__name__)
        d = {}
        if nonEmpty:
            for k, v in self.getAllMetadata().items():
                if v != '':
                    d[k] = v
        pprint.pprint(d if nonEmpty else self.getAllMetadata(), indent=4, width=300)

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
        if dictionary is None:
            return
        for key, value in dictionary.items():
            if base_key != "":
                new_key = "%s.%s" % (base_key, key)
            else:
                new_key = "%s" % key

            if isinstance(value, dict):
                self._iterInDictOfMetadataForUpdate(value, new_key)
            else:
                self.setMetadata(new_key, value)

    @pydantic.validate_arguments
    def _updateMetadata(self, dictionary: Optional[dict]):
        """ 
        Updates metadata's dictionary with a given dictionary
        :param dict dictionary: Dictionary of metadata
        """
        self._iterInDictOfMetadataForUpdate(dictionary, "")

    def updateMetadata(self, dictionary: Optional[dict]):
        """
        Updates metadata's dictionary with a given dictionary
        :param dict dictionary: Dictionary of metadata
        """
        if dictionary:
            self._updateMetadata(dictionary=dictionary)

    def validateMetadata(self, template):
        """
        Validates metadata's dictionary with a given dictionary
        :param dict template: Schema for json template
        """
        if type(template) == pydantic.main.ModelMetaclass:
            template(**self.metadata)
        else:
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


@Pyro5.api.expose
class Data(WithMetadata, BareData):
    """Base class for objects which have metadata and are baredata (serializable)."""
    pass

class Process(BareData,WithMetadata):
    """Base class for objects which have moetadata but are not baredata (non-serializable)."""
    pass


@Pyro5.api.expose
class DataList(Data):
    objs: typing.List[Data]
    dataID: typing.Optional[str] = None
    @staticmethod
    def _seqTypes(seq): return [f'{t.__module__}.{t.__class__.__name__}' for t in seq]

    def __init__(self,*args,**kw):
        if len(args)>1: raise ValueError('Only one non-keyword argument is accepted')
        if len(args)==1:
            if not isinstance(args[0],(list,tuple)): raise ValueError(f'Argument must be a list or tuple (not a {type(args[0])}).')
            if 'objs' in kw: raise ValueError('Both non-keyword sequence and *objs* were specified.')
            kw['objs'] = args[0]
        super().__init__(**kw)
        tset = set(DataList._seqTypes(kw['objs']))
        assert len(tset) <= 1
        # self.dataID = tset.pop()
        self.objs = kw['objs']

    @pydantic.validator('objs')
    def objs_validator(cls, v):
        # if ft:=[e for e in v if not isinstance(e,Data)]: raise ValueError(f'Some objects in the sequence are not a Data (foreign types: {", ".join([t.__module__+t.__class__.__name__ for t in ft])})')
        if len(tset := set(DataList._seqTypes(v))) > 1:
            raise ValueError(f'Multiple Data subclasses in sequence, must be only one ({", ".join([t for t in tset])}).')



