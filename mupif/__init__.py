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

import sys
import importlib
import logging

"""
This is a MuPIF module (Multi-Physics Integration Framework)
"""
# Major.Minor.Patch
__version__ = '2.3.0'
__author__ = 'Borek Patzak, Vit Smilauer, Stanislav Sulc, Martin Horak'


#
# import everything recursively, inject into this module
#
def autoImports():
    import pkgutil
    import os.path
    d = os.path.dirname(os.path.abspath(__file__))
    aa = ['U', 'Q']
    ret = ''
    for loader, modname, ispkg in pkgutil.walk_packages(path=[d], prefix='mupif.'):
        modsplit = modname.split('.')
        # avoid foreign modules
        if modsplit[0] != 'mupif':
            continue
        # avoid mupif itself
        if modsplit == ['mupif']:
            continue
        # important, would mess tests up as they use from mupif import * and such (should not, being nested)
        if modsplit[1] in ('tests', 'physics'):
            continue
        try:
            # important! don't call loader if the modules appeared in sys.modules meanwhile
            # (it could have been imported another module indirectly)
            # this would result in double import with catastrophic consequences
            # such as the same class existing twice, but not being identical
            # print(modname)
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                sys.modules[modname] = (mod := loader.find_module(modname).load_module(modname))
        except Exception as e:
            sys.stderr.write(f'Error importing module {modname}: {str(e)}\n')
            raise
        # direct submodules created as mupif.submodule
        if len(modsplit) == 2:
            aa.append(modsplit[1])
        # contents of those does not need to be exposed as mupif.Class etc
        # if modsplit[1] in ('tests','maybe-something-more'): continue
        # import contents of submodules (direct or indirect)
        names = []
        for name in mod.__dir__():
            # don't export internal names
            if name.startswith('_'):
                continue
            obj = getattr(mod, name)
            # skip builtins and externally imported things
            if not hasattr(obj, '__module__') or not obj.__module__.startswith('mupif.'):
                continue
            # catches classes and enumerations, exactly what we want
            if isinstance(obj, type):
                aa.append(name)
                names.append(name)
        if names:
            ret += f'from .{".".join(modsplit[1:])} import {", ".join(names)}\n'
    ret += f'__all__=[{",".join([repr(a) for a in aa])}]\n'
    return ret


# these are imported explicitly (not classes but rather instances)
from .units import U
from .units import Q

#
# this is the output from mupif.autoImports()
# it must be refreshed by hand whne new class is added or removed
#
from .apierror import APIError
from .bbox import BBox
from .cell import Cell, Triangle_2d_lin, Triangle_2d_quad, Quad_2d_lin, Tetrahedron_3d_lin, Brick_3d_lin
from .constantfield import ConstantField
from .dataid import DataID
from .dumpable import NumpyArray, MupifBaseModel, Dumpable
from .field import FieldType, Field
from .function import Function
from .heavydata import HeavyDataBase, Hdf5RefQuantity, Hdf5OwningRefQuantity, Hdf5HeavyProperty
from .heavystruct import HeavyStruct
from .heavymesh import HeavyUnstructuredMesh
from .integrationrule import IntegrationRule, GaussIntegrationRule
from .jobmanager import JobManException, JobManNoResourcesException, JobManager, RemoteJobManager
from .localizer import Localizer
from .lookuptable import LookupTable
from .lookuptable import MemoryLookupTable
from .mesh import MeshIterator, Mesh, UnstructuredMesh
from .model import Model, RemoteModel
from .multipiecewiselinfunction import MultiPiecewiseLinFunction
from .mupifobject import MupifObjectBase, MupifObject
from .mupifquantity import ValueType, MupifQuantity
from .octree import Octant_py, Octree
from .operatorutil import OperatorInteraction, OperatorEMailInteraction
from .particle import Particle, ParticleSet
from .property import Property, ConstantProperty
from .pyrofile import PyroFile
from .pyroutil import PyroNetConf
from .remoteapprecord import RemoteAppRecord
from .simplejobmanager import SimpleJobManager
from .stringproperty import String
from .timer import Timer
from .timestep import TimeStep
from .units import UnitProxy, Quantity, RefQuantity
from .vertex import Dumpable, Vertex
from .workflow import Workflow
from .workflowmonitor import WorkflowMonitor
from . import pbs_tool

__all__ = ['U','Q','apierror','Dumpable','APIError','bbox','BBox','cell','Dumpable','Cell','Triangle_2d_lin','Triangle_2d_quad','Quad_2d_lin','Tetrahedron_3d_lin','Brick_3d_lin','cellgeometrytype','constantfield','ConstantField','data','dataid','DataID','dumpable','NumpyArray','MupifBaseModel','Dumpable','field','FieldType','Field','function','Function','heavydata','HeavyDataBase','HeavyStruct','Hdf5RefQuantity','Hdf5OwningRefQuantity','HeavyUnstructuredMesh','integrationrule','IntegrationRule','GaussIntegrationRule','jobmanager','JobManException','JobManNoResourcesException','JobManager','RemoteJobManager','localizer','Localizer','mesh','MeshIterator','Mesh','UnstructuredMesh','metadatakeys','model','Model','RemoteModel','mupifobject','MupifObjectBase','MupifObject','mupifquantity','ValueType','MupifQuantity','octree','Octant_py','Octree','operatorutil','OperatorInteraction','OperatorEMailInteraction','particle','Particle','ParticleSet','property','Property','ConstantProperty','stringproperty','String','pyrofile','PyroFile','pyroutil','PyroNetConf','Quantity','remoteapprecord','RemoteAppRecord','simplejobmanager','SimpleJobManager','timer','Timer','timestep','TimeStep','units','UnitProxy','util','vertex','Dumpable','Vertex','workflow','Workflow','workflowmonitor','WorkflowMonitor','lookuptable','LookupTable','MemoryLookupTable','multipiecewiselinfunction','MultiPiecewiseLinFunction','pbs_tool']



# import h5py
import numpy
import serpent
import io

# make flake8 happy
from . import dumpable, util

# can be set to expose PyroFile automatically during serialization, passing the URI to the remote
# (currently unused)
defaultPyroDaemon = None


#
# register all types deriving (directly or indirectly) from Dumpable to Pyro5
#
def _registerDumpable(clss=dumpable.Dumpable):
    import Pyro5.api
    for sub in clss.__subclasses__():
        # print(f'Registering class {sub.__module__}.{sub.__name__}')
        Pyro5.api.register_class_to_dict(sub, dumpable.Dumpable.to_dict)
        Pyro5.api.register_dict_to_class(sub.__module__+'.'+sub.__name__, dumpable.Dumpable.from_dict_with_name)
        _registerDumpable(sub)  # recurse


def _registerOther():
    import Pyro5.api
    # serialize ids if they are sent as top-level objects via Pyro5
    from . import dataid
    c = dataid.DataID
    Pyro5.api.register_class_to_dict(c, dumpable.enum_to_dict)
    Pyro5.api.register_dict_to_class(c.__module__+'.'+c.__name__, dumpable.enum_from_dict_with_name)

    # don't use numpy.ndarray.tobytes as it is not cross-plaform; npy files are
    Pyro5.api.register_class_to_dict(numpy.ndarray, lambda arr: {'__class__': 'numpy.ndarray', 'npy': (numpy.save(buf := io.BytesIO(), arr, allow_pickle=False), buf.getvalue())[1]})
    Pyro5.api.register_dict_to_class('numpy.ndarray', lambda name, dic: numpy.load(io.BytesIO(serpent.tobytes(buf) if isinstance(buf := dic['npy'], dict) else buf), allow_pickle=False))

    def _tryExpose(f):
        if daemon := getattr(f, '_pyroDaemon'):
            return daemon.uriFor(f)
        if defaultPyroDaemon:
            return defaultPyroDaemon.register(f)
        raise RuntimeError(f'{f:s} has no Pyro Damon attached and mupif.defaultPyroDaemon is not defined.')

    Pyro5.api.register_class_to_dict(type, lambda t: {'__class__': 'type', '__module__': t.__module__, '__name__': t.__name__})
    Pyro5.api.register_dict_to_class('type', lambda name, dic: getattr(importlib.import_module(dic['__module__']), dic['__name__']))

    # does not work, as explained in https://github.com/mupif/mupif/issues/32
    # Pyro5.api.register_class_to_dict(PyroFile,lambda f: {'__class__':'mupif.PyroFile','URI':str(_tryExpose(f))})
    # Pyro5.api.register_dict_to_class('mupif.PyroFile',lambda name,dic: Pyro5.api.Proxy(dic['URI']))

    # workaround for msgpack (?)
    # Pyro5.api.register_class_to_dict(tuple,lambda i: dict(val=i))
    # Pyro5.api.register_class_to_dict(h5py.Group,lambda o:{'__class__':'h5py.Group'})
    # Pyro5.api.register_dict_to_class('h5py.Group',lambda _,d: None)
    # Pyro5.api.register_dict_to_class('tuple',lambda _,d: tuple(d['val']))

    Pyro5.api.register_dict_to_class('pydantic.error_wrappers.ValidationError',lambda name,dic: RuntimeError(f'Remote exception name={name}. Traceback:\n'+''.join(dic['attributes']['_pyroTraceback'])))
    Pyro5.api.register_dict_to_class('mupif.apierror.APIError',lambda name,dic: APIError(f'Remote exception name={name}. Traceback:\n'+''.join(dic['attributes']['_pyroTraceback'])))


def _pyroMonkeyPatch():
    import Pyro5.api
    # workaround for https://github.com/irmen/Pyro5/issues/44
    if not hasattr(Pyro5.api.Proxy, '__len__'):
        Pyro5.api.Proxy.__bool__: lambda self: True
        Pyro5.api.Proxy.__len__ = lambda self: self.__getattr__('__len__')()
        Pyro5.api.Proxy.__getitem__ = lambda self, index: self.__getattr__('__getitem__')(index)
        Pyro5.api.Proxy.__setitem__ = lambda self, index, val: self.__getattr__('__setitem__')(index, val)
        Pyro5.api.Proxy.__delitem__ = lambda self, index: self.__getattr__('__delitem__')(index)
        # Pyro5.api.Proxy.__enter__ = lambda self: self.__getattr__('__enter__')()
        # Pyro5.api.Proxy.__exit__ = lambda self,exc_type,exc_value,traceback: self.__getattr__('__exit__')(exc_type,exc_value,traceback)
    

# register all dumpable types
_registerDumpable()
_registerOther()
_pyroMonkeyPatch()

# this is for pydantic
from . import field
field.Field.update_forward_refs()

# configure logging
util.setupLoggingAtStartup()

# switch on optional components
try: util.accelOn()
except ImportError: util.accelOff()
