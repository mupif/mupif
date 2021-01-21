# from mupif.physics import NumberDict
# import mupif.physics.NumberDict

import serpent,enum

# serpent.register_class(enum.IntEnum,lambda obj,ser,ostr,ind: ser._serialize(obj.value,ostr,ind))

class Dumpable(object):
    '''
    Base class for all serializable (dumpable) objects; all objects which are sent over the wire via python must be recursively dumpable, or primitive types. Primitive types are either outside of mupif.* or mupif classes which declare the ``__dumpable_rpimitive__`` tag (class attribute of which value is not relevant).

    Attributes of a dumpable objects are specified via ``dumpAttrs`` class attribute: it is list of attribute names which are to be dumped; the list can be empty, but it is an error if a class about to be dumped does not define it at all.

    Instance is reconstructed by classing the ``__new__`` method of the class (bypassing constructor) and setting all ``dumpAttrs`` directly.

    Inheritance of dumpables i handled by recursion, thus multiple inheritance is supported.

    '''
    dumpAttrs=[]

    def to_dict(self,clss=None):
        import enum
        if not isinstance(self,Dumpable): raise RuntimeError("Not a Dumpable.");
        ret={}
        if clss is None:
            clss=self.__class__
            ret['__class__']=(self.__class__.__module__,self.__class__.__name__)
        # print('%s has dumpAttrs: %s'%(clss.__name__,hasattr(clss,'dumpAttrs')))
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.dumpAttrs:
                if isinstance(attr,tuple): attr,a=attr[0],(attr[1](self) if callable(attr[1]) else attr[1])
                else: a=getattr(self,attr)
                if isinstance(a,Dumpable): ret[attr]=a.to_dict()
                elif isinstance(a,enum.IntEnum): ret[attr]=int(a)
                elif '__dumpable_primitive__' in a.__class__.__dict__: ret[attr]=a
                elif a.__class__.__module__.startswith('mupif.'): raise RuntimeError('%s.%s: type %s does not derive from Dumpable.'%(clss.__name__,attr,a.__class__.__name__))
                else: ret[attr]=a
        else: raise RuntimeError('Class %s.%s does not define dumpAttrs'%(clss.__module__,clss.__name__))
        if clss!=Dumpable:
            for base in clss.__bases__:
                if issubclass(base,Dumpable): ret.update(base.to_dict(self,clss=base))
                else: pass
        return ret


    @staticmethod
    def from_dict(dic,clss=None,obj=None):
        def _create(d):
            if isinstance(d,dict) and '__class__' in d: return Dumpable.from_dict(d)
            else: return d
        if clss is None:
            import importlib
            mod,classname=dic.pop('__class__')
            clss=getattr(importlib.import_module(mod),classname)
            obj=clss.__new__(clss)
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.dumpAttrs:
                if isinstance(attr,tuple): attr=attr[0]
                if attr in dic:
                    setattr(obj,attr,_create(dic.pop(attr)))
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


