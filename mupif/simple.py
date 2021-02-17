import pkgutil
import os.path
d=os.path.dirname(os.path.abspath(__file__))
__all__=[]
for loader,modname,ispkg in pkgutil.walk_packages(path=[d+'/..'],prefix=''):
    # avoid foreign modules
    if not modname.startswith('mupif.'): continue
    # simple prevents recursion, the rest are not real submodules
    if modname.split('.')[1] in ('simple','tests','examples','tools'): continue
    # print(modname)
    mod=loader.find_module(modname).load_module(modname)
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
