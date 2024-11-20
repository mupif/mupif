import enum
import pickle
import serpent
import dataclasses
import importlib
import typing
import numpy
import numpy as np
import Pyro5.api
import sys

import pydantic
import pydantic_core
# from pydantic.dataclasses import dataclass

try:
    import astropy.units
except Exception:
    astropy = None

from typing import Generic, TypeVar

pyd_v0,pyd_v1=pydantic.__version__.split('.')[0:2]
if pyd_v0!='2' and int(pyd_v1)<0:
    raise RuntimeError(f'Pydantic version 2.0.0 or later is required for mupif (upgrade via "pip3 install \'pydantic>=2.0.0\'" or similar); current pydantic version is {pydantic.__version__}')

# for now, disable numpy validation completely until we figure out what works in what python version reliably
if 1:
    NumpyArray = NumpyArrayFloat64 = typing.Any
    NumpyArrayStr = typing.Any
else:
    # TODO: update to pydantic v2?
    # from https://gist.github.com/danielhfrank/00e6b8556eed73fb4053450e602d2434
    from pydantic.fields import ModelField
    DType = TypeVar('DType')
    class NumpyArray(np.ndarray, Generic[DType]):
        """Wrapper class for numpy arrays that stores and validates type information.
        This can be used in place of a numpy array, but when used in a pydantic BaseModel
        or with pydantic.validate_call, its dtype will be *coerced* at runtime to the
        declared type.
        """
        @classmethod
        # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
        # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
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
        NumpyArrayStr = NumpyArray[np.ndarray,typing.Literal['str']]
    except TypeError:
        # python 3.8, just use the generic form
        NumpyArrayFloat64 = NumpyArray


def addPydanticInstanceValidator(klass, makeKlass=None):
    def klass_validate(v):
        if isinstance(v, klass): return v
        if makeKlass: return makeKlass(v)
        else: raise ValueError(f'Instance of {klass.__name__} required (not a {type(v).__name__}).')
    @classmethod
    def klass_get_pydantic_core_schema(cls, source, handler: pydantic.GetCoreSchemaHandler) -> pydantic.GetCoreSchemaHandler:
        return pydantic_core.core_schema.no_info_plain_validator_function(klass_validate)
    klass.__get_pydantic_core_schema__ = klass_get_pydantic_core_schema

class ObjectBase(pydantic.BaseModel,extra='forbid'):
    """Basic configuration of pydantic.BaseModel, common to BareData and also WithMetadata"""

    @Pyro5.api.expose
    @pydantic.validate_call
    def isInstance(self, classinfo: typing.Union[type, typing.Tuple[type, ...]]):
        return isinstance(self, classinfo)

class Utility(ObjectBase):
    '''
    Base class existing for hieararchy structure only. Derived classes provide some
    functionality which does not fit into Process or BareData/Data.
    '''

@Pyro5.api.expose
class BareData(ObjectBase):
    """
    Base class for all serializable (baredata) objects; all objects which are sent over the wire via python must be recursively baredata, basic structures thereof (tuple, list, dict) or primitive types. There are some types handled in a special way, such as enum.IntEnum. Instance is reconstructed by classing the ``__new__`` method of the class (bypassing constructor) and processing ``dumpAttrs``:

    Attributes of a baredata objects are specified via ``dumpAttrs`` class attribute: it is list of attribute names which are to be dumped; the list can be empty, but it is an error if a class about to be dumped does not define it at all. Inheritance of dumpables is handled by recursion, thus multiple inheritance is supported.

    *dumpAttrs* items can take one of the following forms:

    * ``'attr'``: dumped in a simple way
    * ``(attr,val)``: not dumped at all, but set to ``val`` when reconstructed. ``val`` can be callable, in which case it is called with the object as the only argument.
    * ``(attr,store,val)``: dumped with ``store`` (can be callable, in which case it is called with the object as the only argument) and restored with ``val`` (can likewise be callable).

    The ``(attr,val)`` form of ``dumpAttrs`` item can be (ab)used to create a post-processing function, e.g. by saying ``('_postprocess',lambda self: self._postDump())``. Put it at the end of ``dumpAttrs`` to have it called when the reconstruction is about to finish. See :obj:`~mupif.mesh.Mesh` for this usage.

    """
    _pickleInside = False
    model_config = pydantic.ConfigDict(extra='allow')

    # don't pickle attributes starting with underscore
    def __getstate__(self):
        s = super().__getstate__()
        sd = s['__dict__']
        for k in list(sd.keys()):
            if k.startswith('_'):
                sd[k] = None  # del sd[k]
        return s

    def preDumpHook(self):
        'No-op in BareData. Reimplement in derived classes which need special care before being serialized.'
        pass

    def to_dict(self, clss=None):
        def _handle_attr(attr, val, clssName):
            if isinstance(val, list): return [_handle_attr('%s[%d]' % (attr, i), v, clssName) for i, v in enumerate(val)]
            elif isinstance(val, tuple): return tuple([_handle_attr('%s[%d]' % (attr, i), v, clssName) for i, v in enumerate(val)])
            elif isinstance(val, dict): return dict([(k, _handle_attr('%s[%s]' % (attr, k), v, clssName)) for k, v in val.items()])
            elif isinstance(val, BareData): return val.to_dict()
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
                raise RuntimeError('%s.%s: type %s does not derive from BareData.' % (clssName, attr, val.__class__.__name__))
            else:
                return val
        import enum
        if not isinstance(self, BareData): raise RuntimeError("Not a BareData.");
        self.preDumpHook()
        ret = {}
        if clss is None:
            ret['__class__'] = self.__class__.__module__+'.'+self.__class__.__name__
            # XXX: this changed after pydantic V2, so _pickleInside is True even if it is just class attribute?!
            # XXX: and then, FieldInfo has not attribute field_info
            if BareData._pickleInside and False:
                ret['__pickle__'] = pickle.dumps(self)
                return ret
            clss = self.__class__
        if issubclass(clss, pydantic.BaseModel):
            # only dump fields which are registered properly
            for attr,modelField in clss.model_fields.items():
                if modelField.exclude: continue # skip excluded fields
                ret[attr] = _handle_attr(attr, getattr(self, attr), clss.__name__)
        else:
            raise RuntimeError('Class %s.%s is not a pydantic.BaseModel' % (clss.__module__, clss.__name__))
        if clss != BareData:
            for base in clss.__bases__:
                if issubclass(base, BareData):
                    ret.update(base.to_dict(self, clss=base))
                else:
                    pass
        return ret

    def copyRemote(self):
        """
        Create local copy from Pyro's Proxy of this object.

        This abuses the in-band transfer of types in Pyro serializers, thus returning the dictionary with appropriate keys (`__class__` in particular) will automatically deserialize it into an object on the other (local) side of the wire.

        This method does some check whether the object is exposed via Pyro (thus presumable accessed via a Proxy). This cannot be detected reliably, however, thus calling `copyRemote()` on local (unproxied) object will return dictionary rather than a copy of the object.
        """
        # daemon = getattr(self, '_pyroDaemon', None)
        # if not daemon:
        #    raise RuntimeError(f'_pyroDaemon not defined on {str(self)} (not a remote object?)')
        if Pyro5.callcontext.current_context.client is None: raise RuntimeError('This does not seem to be a remote object (context client is None)')
        return self.to_dict()

    def deepcopy(self):
        if Pyro5.callcontext.current_context.client is None: return BareData.from_dict(self.to_dict())
        else: return self.to_dict()
        # return BareData.from_dict(self.to_dict())

    @staticmethod
    def from_dict(dic, clss=None, obj=None):
        def _create(d):
            if isinstance(d, dict) and '__class__' in d: return BareData.from_dict(d)
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
                return astropy.units.Quantity(BareData.from_dict(dic['value']), astropy.units.Unit(dic['unit']))
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
        if clss != BareData:
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
        return BareData.from_dict(dic)

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

    class TestDumpable(BareData):
        num: int = 0
        dic: dict
        recurse: typing.Optional['TestDumpable'] = None

        def __init__(self, **kw):
            print('This is my custom constructor')
            super().__init__(**kw)
            self._myextra = 1
    TestDumpable.model_rebuild()
    td0 = TestDumpable(num=0, dic=dict(a=1, b=2, c=[1, 2, 3]))
    td1 = TestDumpable(num=1, dic=dict(), recurse=td0)
    import pprint
    d1 = td1.model_dump()
    pprint.pprint(d1)
    td1a = TestDumpable.construct(**d1)
    pprint.pprint(td1a.model_dump())
