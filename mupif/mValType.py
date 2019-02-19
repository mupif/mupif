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

import Pyro4
import json
import pprint
import logging
log = logging.getLogger()
    
    
@Pyro4.expose
class MValType:
    def __init__(self, compulsory, types):
        self.compulsory = compulsory
        self.valType = types
    def __repr__(self): #hide details when printing a dictionary
        return str(self.valType) #(self.valType.__name__)


    
def flattenDict(initDict, lkey=''):
    ret = {}
    for rkey,val in initDict.items():
        key = lkey+rkey
        if isinstance(val, dict):
            ret.update(flattenDict(val, key+'.'))
        else:
            ret[key] = val
    return ret
    
        
def compare(MDTemplate, MD, name=''):
    for key, val in MDTemplate.items():
        try:
            if key in MD:
                #print("Template %s=%s Key %s" % (key, val.valType, type(MD.get(key)) ))
                if (type(MD.get(key)) not in val.valType):
                        ss=('Metadata entry %s=%s is of type %s but should be one of %s' % (key, MD.get(key), type(MD.get(key)), val.valType))
                        raise KeyError(ss)
            elif (val.compulsory):
                ss=('Missing metadata key %s in %s' % (key,name.__class__.__bases__))
                raise KeyError(ss)
        except KeyError as error:
            log.exception(error)
            raise
    log.info('Metadata checks passed in %s.' % (name.__class__.__bases__))
        
    
        
