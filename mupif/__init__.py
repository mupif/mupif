#
#               MuPIF: Multi-Physics Integration Framework 
#                   Copyright (C) 2010-2015 Borek Patzak
#
#       Czech Technical University, Faculty of Civil Engineering,
#       Department of Mechanics, 166 29 Prague, Czech Republic
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

"""
This is a MuPIF module (Multi-Physics Integration Framework)
"""
# Major.Minor.Patch
__version__ = '2.3.0'
__author__ = 'Borek Patzak, Vit Smilauer, Stanislav Sulc, Martin Horak'

_branch = 'dev'

import os, sys

from .dataid import FieldID
from .dataid import PropertyID
from .dataid import FunctionID
from .dataid import ParticleSetID
from .valuetype import ValueType

from . import apierror
from . import model
from . import application
from . import bbox
from . import cellgeometrytype
from . import cell
from . import dataid
from . import ensightreader2
from . import field
from . import function
from . import integrationrule
from . import jobmanager
from . import simplejobmanager
from . import localizer
from . import mesh
from . import octree
from . import operatorutil
from . import property
from . import pyroutil
from . import timer
from . import timestep
from . import util
from . import vertex
from . import vtkreader2
from . import remoteapprecord
from . import pyrofile
from . import mupifobject
from . import workflow
from . import metadatakeys
from . import physics
from . import particle
from . import constantfield

# List all submodules, so they can all be imported: from mupif import *
__all__ = [
    # submodules
    'apierror', 'model', 'application', 'bbox', 'cellgeometrytype', 'cell', 'dataid', 'ensightreader2', 'field', 'function', 'integrationrule', 'jobmanager', 'simplejobmanager', 'localizer', 'mesh', 'octree', 'operatorutil', 'property', 'pyroutil', 'timer', 'timestep', 'util', 'valuetype', 'vertex', 'vtkreader2', 'remoteapprecord', 'pyrofile', 'mupifobject', 'workflow', 'metadatakeys', 'physics', 'particle', 'constantfield',
    ##
    # objects imported from submodules
    'FieldID','PropertyID','FunctionID','ParticleSetID','ValueType'
]
from . import util
import logging
import os

# Create default logger
log=util.setupLogger(fileName='mupif.log', level=logging.DEBUG if 'TRAVIS' in os.environ else logging.DEBUG)


##
## register all types deriving (directly or indirectly) from Dumpable to Pyro5
##

def _registerDumpable(clss):
    import Pyro5.api
    for sub in clss.__subclasses__():
        # log.debug(f'Registering class {sub.__module__}.{sub.__name__}')
        Pyro5.api.register_class_to_dict(sub,dumpable.Dumpable.to_dict)
        Pyro5.api.register_dict_to_class(sub.__module__+'.'+sub.__name__,dumpable.Dumpable.from_dict_with_name)
        _registerDumpable(sub) # recurse
    # serialize ids if they are sent as top-level objects via Pyro5
    for c in dataid.FieldID,dataid.ParticleSetID,dataid.FunctionID,dataid.PropertyID:
        Pyro5.api.register_class_to_dict(c,dumpable.enum_to_dict)
        Pyro5.api.register_dict_to_class(c.__module__+'.'+c.__name__,dumpable.enum_from_dict_with_name)

_registerDumpable(dumpable.Dumpable)


