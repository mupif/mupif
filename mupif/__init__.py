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

#
# import everything recursively, inject into this module
#
import pkgutil
import os.path
d=os.path.dirname(os.path.abspath(__file__))
__all__=['U','Q']
for loader,modname,ispkg in pkgutil.walk_packages(path=[d],prefix='mupif.'):
    modsplit=modname.split('.')
    # avoid foreign modules
    if modsplit[0]!='mupif': continue
    # avoid mupif itself
    if modsplit==['mupif']: continue
    # important, would mess tests up as they use from mupif import * and such (should not, being nested)
    if modsplit[1] in ('tests',): continue
    try:
        # important! don't call loader if the modules appeared in sys.modules meanwhile
        # (it could have been imported another module indirectly)
        # this would result in double import with catastrophic consequences
        # such as the same class existing twice, but not being identical
        #print(modname)
        if modname in sys.modules: mod=sys.modules[modname]
        else: sys.modules[modname]=(mod:=loader.find_module(modname).load_module(modname))
    except Exception as e:
        sys.stderr.write(f'Error importing module {modname}: {str(e)}\n')
        raise
    # direct submodules created as mupif.submodule
    if len(modsplit)==2:
        globals()[modsplit[1]]=mod
        __all__.append(modsplit[1])
    # contents of those does not need to be exposed as mupif.Class etc
    #if modsplit[1] in ('tests','maybe-something-more'): continue
    # import contents of submodules (direct or indirect)
    for name in mod.__dir__():
        # don't export internal names
        if name.startswith('_'): continue
        obj=getattr(mod,name)
        # skip builtins and externally imported things
        if not hasattr(obj,'__module__') or not obj.__module__.startswith('mupif.'): continue
        # catches classes and enumerations, exactly what we want
        if isinstance(obj,type):
            globals()[name]=obj
            __all__.append(name)
            # print(name,obj)
# make unique
__all__=list(set(__all__))

U=sys.modules['mupif.physics.physicalquantities'].U
Q=sys.modules['mupif.physics.physicalquantities'].Q

# print([k for k in sys.modules.keys() if k.startswith('mupif.')])

# make flake8 happy
# from . import dumpable, util

##
## register all types deriving (directly or indirectly) from Dumpable to Pyro5
##
def _registerDumpable(clss=dumpable.Dumpable):
    import Pyro5.api
    for sub in clss.__subclasses__():
        # print(f'Registering class {sub.__module__}.{sub.__name__}')
        Pyro5.api.register_class_to_dict(sub,dumpable.Dumpable.to_dict)
        Pyro5.api.register_dict_to_class(sub.__module__+'.'+sub.__name__,dumpable.Dumpable.from_dict_with_name)
        _registerDumpable(sub) # recurse
    # serialize ids if they are sent as top-level objects via Pyro5
    from . import dataid
    for c in dataid.FieldID,dataid.ParticleSetID,dataid.FunctionID,dataid.PropertyID:
        Pyro5.api.register_class_to_dict(c,dumpable.enum_to_dict)
        Pyro5.api.register_dict_to_class(c.__module__+'.'+c.__name__,dumpable.enum_from_dict_with_name)
    # workaround for msgpack (?)
    #Pyro5.api.register_class_to_dict(tuple,lambda i: dict(val=i))
    #Pyro5.api.register_dict_to_class('tuple',lambda _,d: tuple(d['val']))

# register all dumpable types
_registerDumpable()


field.Field.update_forward_refs()


import logging
import os
# Create default logger
log=util.setupLogger(fileName='mupif.log', level=logging.DEBUG if 'TRAVIS' in os.environ else logging.DEBUG)

