import enum
import pickle
import serpent
import dataclasses
import importlib
import typing
import numpy
import numpy as np
import Pyro5
import sys

import pydantic
# from pydantic.dataclasses import dataclass

try:
    import astropy.units
except Exception:
    astropy = None

from typing import Generic, TypeVar
from pydantic.fields import ModelField

if pydantic.__version__.split('.')<['1','9']: raise RuntimeError('Pydantic version 1.9.0 or later is required for mupif (upgrade via "pip3 install \'pydantic>=1.9.0\'" or similar)')

# from https://gist.github.com/danielhfrank/00e6b8556eed73fb4053450e602d2434
DType = TypeVar('DType')
class NumpyArray(np.ndarray, Generic[DType]):
    """Wrapper class for numpy arrays that stores and validates type information.
    This can be used in place of a numpy array, but when used in a pydantic BaseModel
    or with pydantic.validate_arguments, its dtype will be *coerced* at runtime to the
    declared type.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, val, field: ModelField):
        dtype_field = field.sub_fields[0]
        actual_dtype = dtype_field.type_.__args__[0]
        # If numpy cannot create an array with the request dtype, an error will be raised
        # and correctly bubbled up.
        np_array = np.array(val, dtype=actual_dtype)
        return np_array

try:
    # this should work in python 3.9
    # not sure about this?! the first arg is not in the gist, but I get "TypeError: Too few arguments for NumpyArray"
    NumpyArrayFloat64 = NumpyArray[np.ndarray,typing.Literal['float64']]
except TypeError:
    # python 3.8, just use the generic form
    NumpyArrayFloat64 = NumpyArray


def addPydanticInstanceValidator(klass,makeKlass=None):
    def klass_validate(cls,v):
        if isinstance(v,klass): return v
        if makeKlass: return makeKlass(v)
        else: raise TypeError(f'Instance of {klass.__name__} required (not a {type(v).__name__}')
    @classmethod
    def klass_get_validators(cls): yield klass_validate
    klass.__get_validators__=klass_get_validators


class MupifBaseModel(pydantic.BaseModel):
    '''Basic configuration of pydantic.BaseModel, common to Dumpable and also MupifObjectBase'''
    class Config:
        # this is to prevent deepcopies of objects, as some need to be shared (such as Cell.mesh and Field.mesh)
        # see https://github.com/samuelcolvin/pydantic/discussions/2457
        copy_on_model_validation = False
        # this unfortunately also allows arbitrary **kw passed to the ctor
        # but we filter that in the custom __init__ function just below
        # see https://github.com/samuelcolvin/pydantic/discussions/2459
        extra = 'allow'

    def __init__(self, *args, **kw):
        # print('### __init__ with '+str(kw))
        if args:
            raise RuntimeError(f'{self.__class__.__module__}.{self.__class__.__name__}: non-keyword args not allowed in the constructor.')
        # print(kw.keys())
        for k in kw.keys():
            if k not in self.__class__.__fields__:
                raise ValueError(f'{self.__class__.__module__}.{self.__class__.__name__}: field "{k}" is not declared.\n  Valid fields are: {", ".join(self.__class__.__fields__.keys())}.\n  Keywords passed were: {", ".join(kw.keys())}.')
        super().__init__(*args, **kw)


@Pyro5.api.expose
class Dumpable(MupifBaseModel):
    '''
    Base class for all serializable (dumpable) objects; all objects which are sent over the wire via python must be recursively dumpable, basic structures thereof (tuple, list, dict) or primitive types. There are some types handled in a special way, such as enum.IntEnum. Instance is reconstructed by classing the ``__new__`` method of the class (bypassing constructor) and processing ``dumpAttrs``:

    Attributes of a dumpable objects are specified via ``dumpAttrs`` class attribute: it is list of attribute names which are to be dumped; the list can be empty, but it is an error if a class about to be dumped does not define it at all. Inheritance of dumpables is handled by recursion, thus multiple inheritance is supported.

    *dumpAttrs* items can take one of the following forms:

    * ``'attr'``: dumped in a simple way
    * ``(attr,val)``: not dumped at all, but set to ``val`` when reconstructed. ``val`` can be callable, in which case it is called with the object as the only argument.
    * ``(attr,store,val)``: dumped with ``store`` (can be callable, in which case it is called with the object as the only argument) and restored with ``val`` (can likewise be callable).

    The ``(attr,val)`` form of ``dumpAttrs`` item can be (ab)used to create a post-processing function, e.g. by saying ``('_postprocess',lambda self: self._postDump())``. Put it at the end of ``dumpAttrs`` to have it called when the reconstruction is about to finish. See :obj:`~mupif.mesh.Mesh` for this usage.

    '''
    _pickleInside = False

    class Config:
        # this is to prevent deepcopies of objects, as some need to be shared (such as Cell.mesh and Field.mesh)
        # see https://github.com/samuelcolvin/pydantic/discussions/2457
        copy_on_model_validation = False
        # this unfortunately also allows arbitrary **kw passed to the ctor
        # but we filter that in the custom __init__ function just below
        # see https://github.com/samuelcolvin/pydantic/discussions/2459
        extra='allow'

    # don't pickle attributes starting with underscore
    def __getstate__(self):
        s = super().__getstate__()
        sd = s['__dict__']
        for k in list(sd.keys()):
            if k.startswith('_'):
                sd[k] = None  # del sd[k]
        return s

    def to_dict(self, clss=None):
        def _handle_attr(attr, val, clssName):
            if isinstance(val, list): return [_handle_attr('%s[%d]' % (attr, i), v, clssName) for i, v in enumerate(val)]
            elif isinstance(val, tuple): return tuple([_handle_attr('%s[%d]' % (attr, i), v, clssName) for i, v in enumerate(val)])
            elif isinstance(val, dict): return dict([(k, _handle_attr('%s[%s]' % (attr, k), v, clssName)) for k, v in val.items()])
            elif isinstance(val, Dumpable): return val.to_dict()
            elif isinstance(val, enum.Enum): return enum_to_dict(val)
            # explicitly don't handle subtypes
            elif type(val) == numpy.ndarray: return {'__class__': 'numpy.ndarray', 'arr': val.tolist(), 'dtype': str(val.dtype)}
            elif astropy and isinstance(val, astropy.units.UnitBase): return {'__class__': 'astropy.units.Unit', 'unit': val.to_string()}
            elif astropy and isinstance(val, astropy.units.Quantity):
                return {
                    '__class__': 'astropy.units.Quantity',
                    'value': _handle_attr('value', np.array(val.value), val.__class__.__name__),
                    'unit': val.unit.to_string()
                }
            elif val.__class__.__module__.startswith('mupif.'):
                raise RuntimeError('%s.%s: type %s does not derive from Dumpable.' % (clssName, attr, val.__class__.__name__))
            else:
                return val
        import enum
        if not isinstance(self, Dumpable): raise RuntimeError("Not a Dumpable.");
        ret = {}
        if clss is None:
            ret['__class__'] = self.__class__.__module__+'.'+self.__class__.__name__
            if Dumpable._pickleInside:
                ret['__pickle__'] = pickle.dumps(self)
                return ret
            clss = self.__class__
        if issubclass(clss, pydantic.BaseModel):
            # only dump fields which are registered properly
            for attr,modelField in clss.__fields__.items():
                if modelField.field_info.exclude: continue # skip excluded fields
                ret[attr] = _handle_attr(attr, getattr(self, attr), clss.__name__)
        else:
            raise RuntimeError('Class %s.%s is not a pydantic.BaseModel' % (clss.__module__, clss.__name__))
        if clss != Dumpable:
            for base in clss.__bases__:
                if issubclass(base, Dumpable):
                    ret.update(base.to_dict(self, clss=base))
                else:
                    pass
        return ret

    def copyRemote(self):
        '''
        Create local copy from Pyro's Proxy of this object.

        This abuses the in-band transfer of types in Pyro serializers, thus returning the dictionary with appropriate keys (`__class__` in particular) will automatically deserialize it into an object on the other (local) side of the wire.

        This method does some check whether the object is exposed via Pyro (thus presumable accessed via a Proxy). This cannot be detected reliably, however, thus calling `copyRemote()` on local (unproxied) object will return dictionary rather than a copy of the object.
        '''
        daemon = getattr(self, '_pyroDaemon', None)
        if not daemon:
            raise RuntimeError(f'_pyroDaemon not defined on {str(self)} (not a remote object?)')
        return self.to_dict()

    @staticmethod
    def from_dict(dic, clss=None, obj=None):
        def _create(d):
            if isinstance(d, dict) and '__class__' in d: return Dumpable.from_dict(d)
            elif isinstance(d, list): return [_create(d_) for d_ in d]
            elif isinstance(d, tuple): return tuple([_create(d_) for d_ in d])
            elif isinstance(d, dict): return dict([(k, _create(v)) for k, v in d.items()])
            else: return d
        # we saved the inside with pickle, just unpickle here
        if '__pickle__' in dic:
            data = dic['__pickle__']
            if type(data) == dict: data = serpent.tobytes(data)  # serpent serializes bytes in a funny way
            return pickle.loads(data)
        if clss is None:
            import importlib
            mod, classname = dic.pop('__class__').rsplit('.', 1)
            clss = getattr(importlib.import_module(mod), classname)
            # some special cases here
            if issubclass(clss, enum.Enum): return enum_from_dict(clss, dic)
            if astropy and clss == astropy.units.Unit: return astropy.units.Unit(dic['unit'])
            if astropy and clss == astropy.units.Quantity:
                return astropy.units.Quantity(Dumpable.from_dict(dic['value']), astropy.units.Unit(dic['unit']))
            if issubclass(clss, numpy.ndarray):
                if clss != numpy.ndarray: raise RuntimeError('Subclass of numpy.ndarray %s.%s not handled.' % (mod, classname))
                return numpy.array(dic['arr'], dtype=dic['dtype'])
            if issubclass(clss, pydantic.BaseModel): pass
            # print('here D')
            obj = clss.__new__(clss)
        if issubclass(clss, pydantic.BaseModel):
            # print(f'# constructing: {clss.__name__}')
            # print(f'# kw are: {", ".join(dic.keys())}')
            # import pprint
            # pprint.pprint(dic)
            return clss(**dict([(k, _create(v)) for k, v in dic.items()]))
        # this will go
        # if dataclasses.is_dataclass(clss):
        #    for f in dataclasses.fields(clss):
        #        # handles frozen dataclasses as well, hopefully
        #        if f.name in dic: object.__setattr__(obj,f.name,_create(dic.pop(f.name)))
        # recurse into base classes
        if clss != Dumpable:
            for base in clss.__bases__:
                obj.from_dict(dic, clss=base, obj=obj)
        else:
            if len(dic) > 0:
                raise RuntimeError('%d attributes left after deserialization: %s' % (len(dic), ', '.join(dic.keys())))
        return obj

    @staticmethod
    def from_dict_with_name(classname, dic):
        assert classname == dic['__class__']
        # print(f'@@@ {classname} ###')
        return Dumpable.from_dict(dic)

    def dumpToLocalFile(self, filename):
        pickle.dump(self, open(filename, 'wb'))

    @staticmethod
    def loadFromLocalFile(filename):
        return pickle.load(open(filename, 'rb'))


def enum_to_dict(e): return {'__class__': e.__class__.__module__+'.'+e.__class__.__name__, 'name': e.name}


def enum_from_dict(clss, dic): return clss(getattr(clss, dic.pop('name')))


def enum_from_dict_with_name(modClassName, dic):
    mod, className = modClassName.rsplit('.', 1)
    clss = getattr(importlib.import_module(mod), className)
    return clss(getattr(clss, dic.pop('name')))


if __name__ == '__main__':
    import typing

    class TestDumpable(Dumpable):
        num: int = 0
        dic: dict
        recurse: typing.Optional['TestDumpable'] = None

        def __init__(self, **kw):
            print('This is my custom constructor')
            super().__init__(**kw)
            self._myextra = 1
    TestDumpable.update_forward_refs()
    td0 = TestDumpable(num=0, dic=dict(a=1, b=2, c=[1, 2, 3]))
    td1 = TestDumpable(num=1, dic=dict(), recurse=td0)
    import pprint
    d1 = td1.dict()
    pprint.pprint(d1)
    td1a = TestDumpable.construct(**d1)
    pprint.pprint(td1a.dict())
