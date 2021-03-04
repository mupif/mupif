# from mupif.physics import NumberDict
# import mupif.physics.NumberDict

import enum
import pickle
import serpent
import dataclasses
import importlib
import sys
import pprint
import typing

import pydantic
# from pydantic.dataclasses import dataclass

if 0:
    # https://github.com/samuelcolvin/pydantic/issues/116#issue-287220036
    class BaseModelWithPositionalArgs(pydantic.BaseModel):

        def __init__(self, *args, **kwargs):
            pos_args = list(self.__fields__.keys())
            # sys.stderr.write(str(self.__class__.__name__)+':'+str(args)+" | "+str(kwargs)+'\n')

            for i in range(len(args)):
                if i >= len(pos_args):
                    raise TypeError(f'__init__ takes {len(pos_args)} '
                                    'positional arguments but 2 were given.')
                name = pos_args[i]
                if name in kwargs:
                    raise TypeError(f'{name} cannot be both a keyword and '
                                    'positional argument.')
                kwargs[name] = args[i]
            # sys.stderr.write('\n\n'+str(super())+': '+pprint.pformat(kwargs)+'\n\n')
            return super().__init__(**kwargs)



class Dumpable(pydantic.BaseModel):
    '''
    Base class for all serializable (dumpable) objects; all objects which are sent over the wire via python must be recursively dumpable, basic structures thereof (tuple, list, dict) or primitive types. There are some types handled in a special way, such as enum.IntEnum. Instance is reconstructed by classing the ``__new__`` method of the class (bypassing constructor) and processing ``dumpAttrs``:

    Attributes of a dumpable objects are specified via ``dumpAttrs`` class attribute: it is list of attribute names which are to be dumped; the list can be empty, but it is an error if a class about to be dumped does not define it at all. Inheritance of dumpables is handled by recursion, thus multiple inheritance is supported.

    *dumpAttrs* items can take one of the following forms:

    * ``'attr'``: dumped in a simple way
    * ``(attr,val)``: not dumped at all, but set to ``val`` when reconstructed. ``val`` can be callable, in which case it is called with the object as the only argument.
    * ``(attr,store,val)``: dumped with ``store`` (can be callable, in which case it is called with the object as the only argument) and restored with ``val`` (can likewise be callable).

    The ``(attr,val)`` form of ``dumpAttrs`` item can be (ab)used to create a post-processing function, e.g. by saying ``('_postprocess',lambda self: self._postDump())``. Put it at the end of ``dumpAttrs`` to have it called when the reconstruction is about to finish. See :obj:`~mupif.mesh.Mesh` for this usage.

    '''
    _pickleInside=False

    class Config:
        # this is to prevent deepcopies of objects, as some need to be shared (such as Cell.mesh and Field.mesh)
        # see https://github.com/samuelcolvin/pydantic/discussions/2457
        copy_on_model_validation = False
        # this unfortunately also allows arbitrary **kw passed to the ctor
        # but we filter that in the custom __init__ function just below
        # see https://github.com/samuelcolvin/pydantic/discussions/2459
        extra='allow'

    def __init__(self,*args,**kw):
        # print('### __init__ with '+str(kw))
        if args: raise RuntimeError(f'{self.__class__.__module__}.{self.__class__.__name__}: non-keyword args not allowed in the constructor.')
        # print(kw.keys())
        for k in kw.keys():
            if k not in self.__class__.__fields__:
                raise ValueError(f'{self.__class__.__module__}.{self.__class__.__name__}: field "{k}" is not declared.\n  Valid fields are: {", ".join(self.__class__.__fields__.keys())}.\n  Keywords passed were: {", ".join(kw.keys())}.')
        super().__init__(*args,**kw)

    # don't pickle attributes starting with underscore
    def __getstate__(self):
        s=super().__getstate__()
        sd=s['__dict__']
        for k in list(sd.keys()):
            if k.startswith('_'): sd[k]=None # del sd[k]
        return s


    def to_dict(self,clss=None):
        def _handle_attr(attr,val,clssName):
            if isinstance(val,list): return [_handle_attr('%s[%d]'%(attr,i),v,clssName) for i,v in enumerate(val)]
            elif isinstance(val,tuple): return tuple([_handle_attr('%s[%d]'%(attr,i),v,clssName) for i,v in enumerate(val)])
            elif isinstance(val,dict): return dict([(k,_handle_attr('%s[%s]'%(attr,k),v,clssName)) for k,v in val.items()])
            elif isinstance(val,Dumpable): return val.to_dict()
            elif isinstance(val,enum.Enum): return enum_to_dict(val)
            elif val.__class__.__module__.startswith('mupif.'): raise RuntimeError('%s.%s: type %s does not derive from Dumpable.'%(clssName,attr,val.__class__.__name__))
            else: return val
        import enum
        if not isinstance(self,Dumpable): raise RuntimeError("Not a Dumpable.");
        ret={}
        if clss is None:
            ret['__class__']=self.__class__.__module__+'.'+self.__class__.__name__
            if Dumpable._pickleInside:
                ret['__pickle__']=pickle.dumps(self)
                return ret
            clss=self.__class__
        if issubclass(clss,pydantic.BaseModel):
            # only dump fields which are registered properly
            for attr in clss.__fields__.keys():
                ret[attr]=_handle_attr(attr,getattr(self,attr),clss.__name__)
        # this will go
        elif dataclasses.is_dataclass(clss):
            for f in dataclasses.fields(clss):
                if f.metadata and f.metadata.get('mupif_nodump',False)==True: continue
                ret[f.name]=_handle_attr(f.name,getattr(self,f.name),clss.__name__)
        else: raise RuntimeError('Class %s.%s is not a pydantic.BaseModel and not a dataclass'%(clss.__module__,clss.__name__))
        if clss!=Dumpable:
            for base in clss.__bases__:
                if issubclass(base,Dumpable): ret.update(base.to_dict(self,clss=base))
                else: pass
        return ret


    @staticmethod
    def from_dict(dic,clss=None,obj=None):
        def _create(d):
            if isinstance(d,dict) and '__class__' in d: return Dumpable.from_dict(d)
            elif isinstance(d,list): return [_create(d_) for d_ in d]
            elif isinstance(d,tuple): return tuple([_create(d_) for d_ in d])
            elif isinstance(d,dict): return dict([(k,_create(v)) for k,v in d.items()])
            else: return d
        # we saved the inside with pickle, just unpickle here
        if '__pickle__' in dic:
            data=dic['__pickle__']
            if type(data)==dict: data=serpent.tobytes(data) # serpent serializes bytes in a funny way
            return pickle.loads(data)
        if clss is None:
            import importlib
            mod,classname=dic.pop('__class__').rsplit('.',1)
            clss=getattr(importlib.import_module(mod),classname)
            # some special cases here
            if issubclass(clss,enum.Enum): return enum_from_dict(clss,dic)
            if issubclass(clss,pydantic.BaseModel): pass
            if dataclasses.is_dataclass(clss):
                kw=dict([(k,_create(v)) for k,v in dic.items()])
                kw.update(dict([(f.name,None) for f in dataclasses.fields(clss) if f.metadata and f.metadata.get('mupif_nodump',False)==True]))
                return clss(**kw)
            else: obj=clss.__new__(clss)
        if issubclass(clss,pydantic.BaseModel):
            #print(f'# constructing: {clss.__name__}')
            #print(f'# kw are: {", ".join(dic.keys())}')
            return clss(**dict([(k,_create(v)) for k,v in dic.items()]))
        # this will go
        if dataclasses.is_dataclass(clss):
            for f in dataclasses.fields(clss):
                # handles frozen dataclasses as well, hopefully
                if f.name in dic: object.__setattr__(obj,f.name,_create(dic.pop(f.name)))
        # recurse into base classes
        if clss!=Dumpable:
            for base in clss.__bases__:
                obj.from_dict(dic,clss=base,obj=obj)
        else:
            if len(dic)>0: raise RuntimeError('%d attributes left after deserialization: %s'%(len(dic),', '.join(dic.keys())))
        return obj

    @staticmethod
    def from_dict_with_name(classname,dic):
        assert classname==dic['__class__']
        # print(f'@@@ {classname} ###')
        return Dumpable.from_dict(dic)

    def dumpToLocalFile(self,filename):
        pickle.dump(self,open(filename,'wb'))
    @staticmethod
    def loadFromLocalFile(filename):
        return pickle.load(open(filename,'rb'))


def enum_to_dict(e): return {'__class__':e.__class__.__module__+'.'+e.__class__.__name__,'value':e.value}
def enum_from_dict(clss,dic): return clss(dic.pop('value'))
def enum_from_dict_with_name(modClassName,dic):
    mod,className=modClassName.rsplit('.',1)
    clss=getattr(importlib.import_module(mod),className)
    return clss(dic.pop('value'))

if __name__=='__main__':
    import typing
    class TestDumpable(Dumpable):
        num: int=0
        dic: dict
        recurse: typing.Optional['TestDumpable']=None
        def __init__(self,**kw):
            print('This is my custom constructor')
            super().__init__(**kw)
            self._myextra=1
    TestDumpable.update_forward_refs()
    td0=TestDumpable(num=0,dic=dict(a=1,b=2,c=[1,2,3]))
    td1=TestDumpable(num=1,dic=dict(),recurse=td0)
    import pprint
    d1=td1.dict()
    pprint.pprint(d1)
    td1a=TestDumpable.construct(**d1)
    pprint.pprint(td1a.dict())
    
