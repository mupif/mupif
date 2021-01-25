# from mupif.physics import NumberDict
# import mupif.physics.NumberDict

import enum
import pickle
import serpent
import dataclasses



class Dumpable(object):
    '''
    Base class for all serializable (dumpable) objects; all objects which are sent over the wire via python must be recursively dumpable, basic structures thereof (tuple, list, dict) or primitive types. There are some types handled in a special way, such as enum.IntEnum. Instance is reconstructed by classing the ``__new__`` method of the class (bypassing constructor) and processing ``dumpAttrs``:

    Attributes of a dumpable objects are specified via ``dumpAttrs`` class attribute: it is list of attribute names which are to be dumped; the list can be empty, but it is an error if a class about to be dumped does not define it at all. Inheritance of dumpables is handled by recursion, thus multiple inheritance is supported.

    *dumpAttrs* items can take one of the following forms:

    * ``'attr'``: dumped in a simple way
    * ``(attr,val)``: not dumped at all, but set to ``val`` when reconstructed. ``val`` can be callable, in which case it is called with the object as the only argument.
    * ``(attr,store,val)``: dumped with ``store`` (can be callable, in which case it is called with the object as the only argument) and restored with ``val`` (can likewise be callable).

    The ``(attr,val)`` form of ``dumpAttrs`` item can be (ab)used to create a post-processing function, e.g. by saying ``('_postprocess',lambda self: self._postDump())``. Put it at the end of ``dumpAttrs`` to have it called when the reconstruction is about to finish. See :obj:`~mupif.mesh.Mesh` for this usage.

    '''
    dumpAttrs=[]

    pickleInside=False

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
            if Dumpable.pickleInside:
                ret['__pickle__']=pickle.dumps(self)
                return ret
            clss=self.__class__
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.__dict__['dumpAttrs']:
                if isinstance(attr,tuple):
                    if len(attr)==2: continue # not serialized at all
                    assert len(attr)==3
                    attr,a=attr[0],(attr[1](self) if callable(attr[1]) else attr[1])
                else: a=getattr(self,attr)
                ret[attr]=_handle_attr(attr,a,clss.__name__)
        elif dataclasses.is_dataclass(clss):
            for f in dataclasses.fields(clss):
                if not f.repr: continue
                ret[f.name]=_handle_attr(f.name,getattr(self,f.name),clss.__name__)
        else: raise RuntimeError('Class %s.%s does not define dumpAttrs and is not a dataclass'%(clss.__module__,clss.__name__))
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
        if '__pickle__' in dic:
            data=dic['__pickle__']
            if type(data)==dict: data=serpent.tobytes(data)
            return pickle.loads(data)
        if clss is None:
            import importlib
            mod,classname=dic.pop('__class__').rsplit('.',1)
            clss=getattr(importlib.import_module(mod),classname)
            # some special cases here
            if issubclass(clss,enum.Enum): return enum_from_dict(clss,dic)
            if dataclasses.is_dataclass(clss):
                kw=dict([(k,_create(v)) for k,v in dic.items()])
                kw.update(dict([(f.name,None) for f in dataclasses.fields(clss) if f.repr==False]))
                return clss(**kw)
            else: obj=clss.__new__(clss)
        # mupif classes
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.__dict__['dumpAttrs']:
                if isinstance(attr,tuple):
                    if len(attr)==2:
                        if callable(attr[1]): attr[1](obj)
                        else: setattr(obj,attr[0],attr[1])
                        continue
                    assert len(attr)==3
                    if not attr[0] in dic: continue
                    if callable(attr[2]): attr[2](obj,dic.pop(attr[0]))
                    else: setattr(obj,attr[0],attr[2])
                else:
                    if attr in dic: setattr(obj,attr,_create(dic.pop(attr)))
        elif dataclasses.is_dataclass(clss):
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
        return Dumpable.from_dict(dic)


def enum_to_dict(e): return {'__class__':e.__class__.__module__+'.'+e.__class__.__name__,'value':e.value}
def enum_from_dict(clss,dic): return clss(dic.pop('value'))
def enum_from_dict_with_name(modClassName,dic):
    mod,className=modClassName.rsplit('.',1)
    clss=getattr(importlib.import_module(mod),className)
    return clss(dic.pop('value'))
