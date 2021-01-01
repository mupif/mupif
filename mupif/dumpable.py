# from mupif.Physics import NumberDict
# import mupif.Physics.NumberDict

class Dumpable(object):
    dumpAttrs=[]

    def to_dict(self,clss=None):
        import enum
        if not isinstance(self,Dumpable): raise RuntimeError("Not a Dumpable.");
        ret={}
        if clss is None:
            clss=self.__class__
            ret['__mupif_class__']=(self.__class__.__module__,self.__class__.__name__)
        # print('%s has dumpAttrs: %s'%(clss.__name__,hasattr(clss,'dumpAttrs')))
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.dumpAttrs:
                a=getattr(self,attr)
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
            if isinstance(d,dict) and '__mupif_class__' in d: return Dumpable.from_dict(d)
            else: return d
        if clss is None:
            import importlib
            mod,classname=dic.pop('__mupif_class__')
            clss=getattr(importlib.import_module(mod),classname)
            obj=clss.__new__(clss)
        if 'dumpAttrs' in clss.__dict__:
            for attr in clss.dumpAttrs:
                if attr in dic:
                    setattr(obj,attr,_create(dic.pop(attr)))
        if clss!=Dumpable:
            for base in clss.__bases__:
                obj.from_dict(dic,clss=base,obj=obj)
        else:
            if len(dic)>0: raise RuntimeError('%d attributes left after deserialization: %s'%(len(dic),', '.join(dic.keys())))
        return obj

