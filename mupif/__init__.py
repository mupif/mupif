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

if 'MUPIF_PYRO5' in os.environ:
    from Pyro5.compatibility import Pyro4
    sys.modules['Pyro4']=Pyro4
    import mupif.compat
    pyroVer=5
else:
    pyroVer=4


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
    # objects imported from submodules
    'FieldID','PropertyID','FunctionID','ParticleSetID','ValueType'
]
from . import util
import logging
import os

# Create default logger
util.setupLogger(fileName='mupif.log', level=logging.DEBUG if 'TRAVIS' in os.environ else logging.DEBUG)

# # temporarily disabled (does not work on travis, even though future is installed there??)
# # more helpful error message
# try: import future, builtins
# except ImportError:
# 	print("ERROR: mupif requires builtins and future modules; install both via 'pip install future'")
# 	raise
