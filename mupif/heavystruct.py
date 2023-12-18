import dataclasses
from dataclasses import dataclass
from typing import Any
import typing
import sys
import numpy as np
import h5py
import Pyro5.api
# metadata support
# from .data import Data
from . import units, pyroutil, baredata, field
from . import dataid
from .heavydata import HeavyDataBase, HeavyDataBase_ModeChoice, HeavyConvertible
from .pyrofile import PyroFile
import types
import json
import tempfile
import logging
import os
import pydantic
import subprocess
import shutil
import itertools
import numbers
log = logging.getLogger(__name__)


false=False # for JS compat in schema here

HeavyStructSchemaModel={
    '$schema':'https://json-schema.org/draft/2020-12/schema',
    '$id':'https://mupif.org/heavystruct-example.schema.json',
    'title':'HeavyStruct',
    'description':'HeavyStruct schema',
    'type':'array',
    'items':{
        'type':'object',
        'required':['_schema','_datasetName'],
        'properties':{
            '_schema': {
                'type':'object',
                'properties':{
                    'name':   {'type':'string','description':'Free-form identifier of the schema.'},
                    'version':{'type':'string','description':'Free-form version of the schema.'},
                },
                'required':['name','version']
            },
            '_datasetName':{'type':'string','description':'Nested dataset name for storing objects belonging to this schema'},
            'additionalProperties':{
                'type':'object',
                '$ref':'#/$defs/heavyprop',
            },
        }
    },
    '$defs':{
        'heavyprop':{
            'oneOf':[
                {'type':'object',
                    'properties':{
                        'dtype':{'type':'string','pattern':'^(l|d|\\?|f|(a|S)[0-9]*|json|object)$','description':'Numpy datatype'},
                        'unit':{'type':'string','description':'Unit in the Astropy format'},
                        'shape':{'oneOf':[{'type':['array','string'],'items':{'type':'integer'}},{'const':'variable'}]},
                        'choice':{'type':['array'],'items':{'type':'string'}},
                        'key':{'type':'string'},
                        'lookup':{'type':'object'},
                        'delim':{'type':'string'},
                    },
                    'additionalProperties':false,
                },
                {'type':'object',
                    'properties':{
                        'path':{'type':'string'},
                        'schema':{'type':'string'}
                    },
                    'required':['path','schema'],
                    'additionalProperties':false,
                }
            ]
        }
    }
}

sampleSchemas_json = '''
[
    {
        "_schema": {
            "name": "org.mupif.sample.atom",
            "version": "1.0"
        },
        "_datasetName": "atoms",
        "identity": {
            "element": {
                "dtype": "a2"
            },
            "atomicNumber": {
                "dtype": "l",
                "key": "identity.element",
                "lookup": {
                    "H": 1,
                    "C": 6,
                    "N": 7,
                    "Na": 11,
                    "Cl": 17,
                    "Fe": 26
                }
            },
            "atomicMass": {
                "dtype": "f",
                "key": "identity.element",
                "unit": "Dalton",
                "lookup": {
                    "H": 1.0079,
                    "C": 12.0107,
                    "N": 14.0067,
                    "Na": 22.9897,
                    "Cl": 35.453,
                    "Fe": 55.845
                }
            }
        },
        "properties": {
            "physical": {
                "partialCharge": {
                    "neutral": {
                        "dtype": "d",
                        "unit": "e"
                    },
                    "anion": {
                        "dtype": "d",
                        "unit": "e"
                    },
                    "cation": {
                        "dtype": "d",
                        "unit": "e"
                    }
                },
                "polarizability": {
                    "neutral": {
                        "dtype": "d",
                        "unit": "AA^2 s^4 kg^-1"
                    },
                    "anion": {
                        "dtype": "d",
                        "unit": "AA^2 s^4 kg^-1"
                    },
                    "cation": {
                        "dtype": "d",
                        "unit": "AA^2 s^4 kg^-1"
                    }
                }
            },
            "topology": {
                "parent": {
                    "dtype": "l"
                },
                "type": {
                    "dtype": "a"
                },
                "name": {
                    "dtype": "a"
                },
                "position": {
                    "dtype": "d",
                    "shape": [
                        3
                    ],
                    "unit": "AA"
                },
                "velocity": {
                    "dtype": "d",
                    "shape": [
                        3
                    ],
                    "unit": "AA/ps"
                },
                "structure": {
                    "dtype": "l",
                    "shape": "variable"
                }
            }
        }
    },
    {
        "_schema": {
            "name": "org.mupif.sample.molecule",
            "version": "1.0"
        },
        "_datasetName": "molecules",
        "identity": {
            "chemicalName": {
                "dtype": "a"
            },
            "molecularWeight": {
                "dtype": "d",
                "unit": "Dalton"
            }
        },
        "properties": {
            "electrical": {
                "HOMO": {
                    "dtype": "d",
                    "unit": "eV"
                },
                "LUMO": {
                    "dtype": "d",
                    "unit": "eV"
                },
                "siteEnergy": {
                    "orbital": {
                        "dtype": "d",
                        "unit": "eV"
                    },
                    "electrostatic": {
                        "dtype": "d",
                        "unit": "eV"
                    },
                    "polarization": {
                        "dtype": "d",
                        "unit": "eV"
                    }
                },
                "transferIntegrals": {
                    "dtype": "d",
                    "shape": "variable"
                },
                "reorganizationEnergyInternal": {
                    "anion": {
                        "dtype": "d",
                        "unit": "eV"
                    },
                    "cation": {
                        "dtype": "d",
                        "unit": "eV"
                    }
                }
            },
            "physical": {
                "polarizability": {
                    "neutral": {
                        "dtype": "d",
                        "shape": [
                            3,
                            3
                        ],
                        "unit": "AA^2 s^4 kg^-1"
                    },
                    "anion": {
                        "dtype": "d",
                        "shape": [
                            3,
                            3
                        ],
                        "unit": "AA^2 s^4 kg^-1"
                    },
                    "cation": {
                        "dtype": "d",
                        "shape": [
                            3,
                            3
                        ],
                        "unit": "AA^2 s^4 kg^-1"
                    }
                }
            },
            "chemical": {}
        },
        "topology": {
            "parent": {
                "dtype": "l",
                "unit": "none"
            },
            "centerOfMass": {
                "dtype": "d",
                "shape": [
                    3
                ],
                "unit": "AA"
            },
            "symmetryAxis": {
                "dtype": "d",
                "shape": [
                    3
                ],
                "unit": "AA"
            },
            "structureNeighbors": {
                "dtype": "l",
                "shape": "variable"
            }
        },
        "implementation": {
            "forceFieldType": {
                "dtype": "a"
            }
        },
        "atoms": {
            "path": "molecule/{ROW}/",
            "schema": "org.mupif.sample.atom"
        }
    },
    {
        "_schema": {
            "name": "org.mupif.sample.grain",
            "version": "1.0"
        },
        "_datasetName": "grains",
        "identity": {
            "material": {
                "dtype": "a"
            }
        },
        "properties": {
            "eletrical": {
                "freeElectrons": {
                    "dtype": "l",
                    "unit": "none"
                },
                "freeHoles": {
                    "dtype": "l",
                    "unit": "none"
                }
            },
            "physical": {
                "reorganizationEnergyExternal": {
                    "dtype": "d",
                    "unit": "eV"
                }
            },
            "chemical": {},
            "symmetry": { "choice":["none","axial","periodic","translational","rotational"] }
        },
        "topology": {
            "parent": {
                "dtype": "l"
            },
            "cellSize": {
                "dtype": "d",
                "shape": [
                    3
                ],
                "unit": "m"
            }
        },
        "implementation": {
            "boundaryCondition": {
                "dtype": "a"
            }
        },
        "molecules": {
            "path": "grain/{ROW}/",
            "schema": "org.mupif.sample.molecule"
        }
    }
]
'''

## XXX: field utility functions

def _mupif_to_hdf5_group__return_index(*,grp,obj):
    # assert isinstance(obj,HeavyConvertible)
    if not isinstance(obj,HeavyConvertible): raise TypeError(f'Object {obj} of type {obj.__class__.__name__} not not a mupif.HeavyConvertible.')
    # assert isinstance(obj,field.Field)
    # return obj.toHdf5(h5group=grp)
    return obj.copyToHeavy(h5grp=grp)

def _mupif_from_hdf5_group(*,grp:h5py.Group,index:int,storedType:str):
    # TODO: determine type to be restored, for now just assume Field
    if storedType=='mupif.Field': return field.Field.makeFromHeavy(h5grp=grp,indices=[index])[0]
    else: raise TypeError(f'Unhandled stored type {storedType} in HeavyStruct.')
    # return field.Field.makeFromHeavydf5(h5group=grp,indices=[index])[0]


def _cookSchema(desc, prefix='', schemaName='', fakeModule='', datasetName='', namingConvention='get-set'):
    __doc0__ = '''
    Transform dictionary-structured data schema into context access types.
    The access types are created using the "type" builtin and only stored
    in closures of the functions returning them. The top-level context is
    returned from this function to the user.
    
    get/set methods (and others) are not created on the fly but are instead
    put into those context types. This is substantially more efficient than
    hijacking __getattr__ and __setattr__.
    
    Closures in Python are somewhat unintuitive, since e.g. loop does not
    create a new scope (thus variable reference would later have the value
    in the last iteration step). Therefore local variables are captured via
    local function defaults, which makes some of the code less readable.
    '''

    @dataclass
    class CookedSchemaFragment:
        'Internal data used when cookSchema is called recursively'
        dtypes: list    # accumulates numpy dtypes for compound datatype
        defaults: dict  # default values, nan for floats and 0 for integers
        subpaths: dict  # accumulates nested paths (for deletion when resizing), as (path,schema) tuple, keyed by FQ
        units: dict     # accumulates units for normal values types (for dict export), keyed by FQ
        T: Any = None   # nested context type
        doc: typing.List[str] = dataclasses.field(default_factory=list)  # accumulates documentation (as markdown nested list)

        def append(self, other):
            self.dtypes += other.dtypes
            self.defaults.update(other.defaults)
            self.doc += other.doc
            self.subpaths.update(other.subpaths)
            self.units.update(other.units)

    def dtypeUnitDefaultDoc(v):
        'Parse dictionary *v* (part of the schema) and return (dtype,unit,default,doc) tuple'
        shape = v['shape'] if 'shape' in v else ()
        if isinstance(shape, list):
            shape = tuple(shape)
        ddoc = {}
        if shape:
            ddoc['shape'] = f'[{"×".join([str(s) for s in shape])}]'
        unit = units.Unit(v['unit']) if 'unit' in v else None
        dtype = v['dtype']
        default = None
        if dtype == 'json':
            dtype=h5py.string_dtype(encoding='utf-8')
            if shape: raise RuntimeError(f'Shape must NOT be specified with dtype="json".')
            ddoc['dtype']='data with automatic json conversion (stored as dynamic utf-8 string)'
            ddoc['shape']='dynamic'
        elif (dt:=np.dtype(dtype)).char in ('a','S'):
            # use special h5py type for dynamic strings
            if dt.itemsize==0: dtype = h5py.string_dtype(encoding='utf-8')
            # use numpy dtype for static-size strings
            else: dtype = dt
            if shape: raise RuntimeError(f'Shape must NOT be specified with string types (shape: {shape}, dtype: {dtype}).')
            if 'delim' not in v: ddoc['dtype'] = 'string (utf-8 encoded)'
            else:
                if not isinstance(v['delim'],str) or len(v['delim'])<1: raise RuntimeError('*delim* must be a str instance with length at least 1.')
                ddoc['type'] = 'string list (internal delimiter "{v["delim"]}")'
            ddoc['shape'] = ('dynamic' if dt.itemsize==0 else '≤ {dt.itemsize} chars')
        elif shape == 'variable':
            ddoc['dtype'] = f'`[{np.dtype(dtype).name},…]`'
            dtype = h5py.vlen_dtype(np.dtype(dtype))
            shape = None
            ddoc['shape'] = 'dynamic'
        else:
            dtype = np.dtype((dtype, shape))
            # log.warning(f'{fq}: defaults for non-scalar quantities (dtype.subdtype) not yet supported.')
            basedtype = (dtype if (not hasattr(dtype, 'subdtype') or dtype.subdtype is None) else dtype.subdtype[0])
            # basedtype=dtype # workaround
            if basedtype.kind == 'f':
                default = np.nan
            elif basedtype.kind in 'iu':
                default = 0
            ddoc['dtype'] = f'`{basedtype.name}`'
        if 'delim' in v and dt.char not in ('a','S'): raise RuntimeError('*delim* can only be specified with string dtype (dynamic or static)')
        if unit:
            ddoc['unit'] = f"`{str(unit)}`"
        if 'lookup' in v:
            ddoc['read-only'] = f'table look-up by `{v["key"]}`'
            default = None
        if default is not None:
            ddoc['default'] = f"`{str(default)}`"
        return dtype, unit, default, ', '.join(f'{k}: {v}' for k, v in ddoc.items())

    def capitalize(k):
        'Turn the first letter into uppercase'
        return k[0].upper()+k[1:]

    def setEntireDatasetRow_changeOneItem(*,ds,row,fq,val):
        # workaround for bugs in h5py: for variable-length fields, and dim>1 subarrays:
        # direct assignment does not work; must read the whole row, modify, write it back
        # see https://stackoverflow.com/q/67192725/761090 and https://stackoverflow.com/q/67451714/761090
        rowdata=ds[row]
        # rowdata[ds.dtype.names.index(fq)]=val # this does not seem to be needed (anymore?)
        rowdata[fq]=val
        ds[row]=rowdata
    def addAccessors(meth,attr,getter,setter=None):
        if namingConvention=='get-set':
            meth['get'+capitalize(attr)]=getter
            if setter: meth['set'+capitalize(attr)]=setter
        elif namingConvention=='property':
            meth[attr]=property(fget=getter,fset=setter)
        else: raise RuntimeError(f'namingConvention must be "get-set" or "property" (not "{namingConvention}").')
    def makeDoc(key,doc,ro=False):
        if namingConvention=='get-set':
            if ro: ret=" `get{capitalize(key)}()`: "+doc
            else:  ret=" `get{capitalize(key)}()`, `set{capitalize(key)}(…)`: "+doc
        elif namingConvention=='property':
            if ro: ret=" `key` [read-only]: "+doc
            else:  ret=" `key` [read-write]: "+doc
        return ret


    ret = CookedSchemaFragment(dtypes=[], defaults={}, subpaths={}, units={})
    meth = {} # accumulate attribute access methods
    docLevel = (0 if not schemaName else prefix.count('.')+1)

    # top-level only
    if not schemaName:
        schemaName = desc['_schema']['name']
        schemaVersion = desc['_schema'].get('version','<unspecified>')
        namingConvention=desc['_schema'].get('naming',namingConvention)
        datasetName = desc.get('_datasetName',schemaName)
        assert len(prefix) == 0
        T_name = 'Context_'+schemaName.replace('.', '_')
        import hashlib
        h = hashlib.blake2b(digest_size=6)
        h.update(json.dumps(desc).encode('utf-8'))
        fakeModule = types.ModuleType('_mupif_heavydata_'+h.hexdigest(), 'Synthetically generated module for mupif.HeavyStruct schemas')
        # this somehow breaks imports, so better to avoid it until understood
        # if fakeModule.__name__ in sys.modules: return getattr(sys.modules[fakeModule.__name__],T_name)
        # sys.modules[fakeModule.__name__]=fakeModule
        ret.doc += [f'**schema {schemaName}**', '']
    else:
        T_name = 'Context_'+schemaName+'_'+prefix.replace('.', '_')
    assert namingConvention in ['get-set','property']

    meth['schema_fragment']=property(fget=lambda self,desc=desc: desc)

    for key, val in desc.items():
        try:
            # fully-qualified name: for messages and compound field name in h5py
            fq = (f"{prefix}.{key}" if prefix else key)
            docHead = docLevel*3*' '+f'* `{key}`'
            # special keys start with underscore, so far only _schema is used
            if key.startswith('_'):
                if key == '_schema':
                    continue
                elif key == '_datasetName':
                    continue
                else:
                    raise ValueError(f"Unrecognized special key '{key}' in prefix '{prefix}'.")
            if not isinstance(val, dict):
                raise TypeError(f"{fq}: value is not a dictionary.")
            # attribute defined via lookup, not stored
            if 'indexed' in val:
                indexName=val['indexed']
                path=val['path']
                ret.doc+=[docHead+': '+makeDoc(key,f'reference indexed by `{indexName}` into group `{path}`.',ro=True)]
                def indexGetter(self, *, fq=fq, indexName=indexName, path=path):
                    if path not in self.ctx.h5group:
                        # dataset to be referenced does not exist yet, find its schema by going through the schema registry
                        ss=[s for s in self.ctx.schemaRegistry.values() if s.datasetName==path]
                        if len(ss)!=1: raise RuntimeError(f'Unable to find unique schema with dataset called {path} (count is {len(ss)}, should be 1).')
                        SchemaT=ss[0]
                    else:
                        refSchema=self.ctx.h5group[path].attrs['schema']
                        SchemaT=self.ctx.schemaRegistry[refSchema]
                    if self.row is None:
                        # returns the entire dataset referenced
                        return SchemaT(top=HeavyStruct.TopContext(h5group=self.ctx.h5group,schemaRegistry=self.ctx.schemaRegistry,pyroIds=self.ctx.pyroIds),row=None)
                    _T_assertDataset(self,f'when looking up index array')
                    index=np.array(self.ctx.dataset[indexName][self.row])
                    indices=([index] if index.ndim==0 else index)
                    ret=[SchemaT(top=HeavyStruct.TopContext(h5group=self.ctx.h5group,schemaRegistry=self.ctx.schemaRegistry,pyroIds=self.ctx.pyroIds),row=idx) for idx in indices]
                    #log.error(f'{index=}, {indices=}, {index.ndim=}')
                    return (ret[0] if index.ndim==0 else ret)
                addAccessors(meth,key,indexGetter)
            elif 'lookup' in val:
                dtype, unit, default, doc = dtypeUnitDefaultDoc(val)
                ret.doc += [docHead+': '+makeDoc(key,doc,ro=True)]
                lKey, lDict = val['key'], val['lookup']
                if isinstance(lKey, bytes):
                    lKey = lKey.decode('utf8')

                # bind local values via default args (closure)
                def inherentGetter(self, *, fq=fq, dtype=dtype, unit=unit, lKey=lKey, lDict=lDict):
                    _T_assertDataset(self, f"when looking up '{fq}' based on '{lKey}'.")

                    def _lookup(row):
                        k=self.ctx.dataset[lKey, row]
                        if isinstance(k, bytes):
                            k = k.decode('utf8')
                        try:
                            val = np.array(lDict[k], dtype=dtype)[()]  # [()] unpacks rank-0 scalar
                        except KeyError:
                            raise KeyError(f"{fq}: key '{k}' ({lKey}) not found in the lookup table with keys {list(lDict.keys())}") from None
                        return val
                    # fake broadcasting
                    if self.row is None:
                        val = np.array([_lookup(r) for r in range(self.ctx.dataset.shape[0])])
                    else:
                        val = _lookup(self.row)
                    if unit:
                        return units.Quantity(value=val, unit=unit)
                    else:
                        return val
                addAccessors(meth,key,inherentGetter)
            elif 'choice' in val:
                choices=val['choice']
                num=0
                str2num,num2str={},{}
                if not isinstance(choices,(list,tuple)): raise TypeError(f"'{fq}': choice must be a sequence")
                for ilabel,label in enumerate(choices):
                    if not isinstance(label,str): raise ValueError(f"'{fq}': choice items must be strings (item {ilabel} is a {type(label).__name__})")
                    if label in str2num: raise ValueError(f"'{fq}': duplicate choice label '{label}'")
                    num2str[num],str2num[label]=label,num
                    num+=1
                mn,mx=min(num2str.keys()),max(num2str.keys())
                # min_scalar_type: signed when mn<0, otherwise unsigned; min_scalar_type should ensure appropriate range
                dtype=(np.min_scalar_type(mx) if mn>=0 else mn.min_scalar_type(-max(abs(mn),abs(mx))))
                ret.dtypes+=[(fq,dtype)]
                ret.doc+=[docHead+': '+makeDoc(key,'named enumeration stored as {dtype.name}: '+', '.join([f'{k} (v)' for k,v in str2num.items()]),ro=False)]
                ret.defaults[fq]=list(num2str.keys())[0] # first key is the default
                ret.units[fq]=None
                def getter(self,*,fq=fq):
                    if self.row is not None: return num2str[self.ctx.dataset[fq,self.row]]
                    else: return [num2str[self.ctx.dataset[fq,r]] for r in range(self.ctx.dataset.shape[0])]
                def setter(self,val,*,fq=fq):
                    if self.row is not None: self.ctx.dataset[fq,self.row]=str2num[val]
                    else: self.ctx.dataset[fq]=np.full(self.ctx.dataset.shape[0],str2num[val])
                addAccessors(meth,key,getter,setter)
            elif 'mupifType' in val: ## XXX experimental
                dtype,unit,default,doc=dtypeUnitDefaultDoc(val)
                if issubclass(dtype.type,numbers.Integral): ndim=0
                elif issubclass(h5py.check_vlen_dtype(dtype).type,numbers.Integral): ndim=1
                else: raise ValueError(f'{fq}: dtype must be integral type, or variable-length integral type')
                ret.dtypes+=[(fq,dtype)]
                mupifObjectGrp='mupif-obj'
                def getter(self,*,fq=fq,dtype=dtype,ndim=ndim,val=val):
                    if self.row is None:
                        raise NotImplementedError(f'{fq}: broadcasting.')
                    if ndim==0:
                        index=self.ctx.dataset[self.row,fq]
                        grp=self.ctx.h5group[mupifObjectGrp]
                        return _mupif_from_hdf5_group(grp=grp,index=index,storedType=val['mupifType'])
                    else:
                        assert ndim==1
                        return [_mupif_from_hdf5_group(grp=self.ctx.h5group[mupifObjectGrp],index=ix,storedType=val['mupifType']) for ix in np.array(self.ctx.dataset[self.row,fq])]
                def setter(self,val,metadata={},*,dtype=dtype,fq=fq,ndim=ndim):
                    if self.row is None: raise NotImplementedError(f'{fq}: broadcasting.')
                    if mupifObjectGrp not in self.ctx.h5group: self.ctx.h5group.create_group(mupifObjectGrp)
                    if ndim==0:
                        index=_mupif_to_hdf5_group__return_index(grp=self.ctx.h5group[mupifObjectGrp],obj=val)
                        self.ctx.dataset[self.row,fq]=index
                    else:
                        assert ndim==1
                        indices=np.array([_mupif_to_hdf5_group__return_index(grp=self.ctx.h5group[mupifObjectGrp],obj=v) for v in val])
                        setEntireDatasetRow_changeOneItem(ds=self.ctx.dataset,row=self.row,fq=fq,val=indices.astype(h5py.check_vlen_dtype(dtype)))
                def appender(self,val,*,dtype=dtype,ndim=ndim,fq=fq):
                    assert ndim==1
                    if mupifObjectGrp not in self.ctx.h5group: self.ctx.h5group.create_group(mupifObjectGrp)
                    newIx=_mupif_to_hdf5_group__return_index(grp=self.ctx.h5group[mupifObjectGrp],obj=val)
                    indices=np.array(self.ctx.dataset[self.row,fq].tolist()+[newIx])
                    setEntireDatasetRow_changeOneItem(ds=self.ctx.dataset,row=self.row,fq=fq,val=indices.astype(h5py.check_vlen_dtype(dtype)))
                addAccessors(meth,key,getter,setter)
                if ndim==1:
                    assert namingConvention=='get-set'
                    meth['append'+capitalize(key)]=appender
            # normal data attribute
            elif 'dtype' in val:
                dtype,unit,default,doc=dtypeUnitDefaultDoc(val)
                basedtype=(b[0] if (b:=getattr(dtype,'subdtype',None)) else dtype)
                delim=val.get('delim',None)
                isJson=(val['dtype']=='json')
                ret.dtypes+=[(fq,dtype)] # add to the compound type
                ret.doc+=[docHead+': '+makeDoc(key,doc)]
                ret.units[fq]=unit
                if default is not None: ret.defaults[fq]=default # add to the defaults
                def getter(self,*,fq=fq,unit=unit,delim=delim,isJson=isJson):
                    _T_assertDataset(self,f"when getting the value of '{fq}'")
                    if self.row is not None: value=self.ctx.dataset[fq,self.row]
                    else: value=self.ctx.dataset[fq]
                    if isinstance(value,bytes): value=value.decode('utf-8')
                    if delim is not None: value=tuple(value.split(delim))
                    if isJson: value=json.loads(value)
                    if unit is None: return value
                    return units.Quantity(value=value,unit=unit)
                def _cookValue(val,*,unit,dtype,basedtype,delim,isJson=False):
                    'Unit conversion, type conversion before assignment'
                    if unit: val=(units.Quantity(val).to(unit)).value
                    if delim is not None:
                        if isinstance(val,(str,bytes)): raise TypeError('String list cannot be set with str/bytes (pass list of chars if this is really what you mean)')
                        for i,v in enumerate(val):
                            if delim in v: raise RuntimeError(f'Item {i} contains delimiter "{delim}".')
                        val=str(delim).join(val)
                    if isJson: val=json.dumps(val)
                    if isinstance(val,str): val=val.encode('utf-8')
                    #sys.stderr.write(f"{fq}: {basedtype}\n")
                    ret=np.array(val).astype(basedtype,casting='safe',copy=False)
                    #log.error(f'{val=}')
                    #log.error(f'{ret=}')
                    #log.error(f'{dtype=} {basedtype=}')
                    #log.error(f'{h5py.check_vlen_dtype(dtype)=}')
                    # for object (variable-length) types, convertibility was checked but the result is discarded
                    if basedtype.kind=='O':
                        # this allows to assign e.g. list like [1,2] rather than requiring np.array([1,2])
                        # int8 is exempted as that would convert strings to numeric arrays, causing error later
                        if (dt2:=h5py.check_vlen_dtype(dtype)) and np.issubdtype(dt2,np.number) and dt2!=np.dtype('int8'): val=np.array(val).astype(dt2,casting='safe')
                        #log.error(f'{val=}')
                        return val 
                    #sys.stderr.write(f"{fq}: cook {val} → {ret}\n")
                    return ret
                def setter_direct(self,val,*,fq=fq,unit=unit,dtype=dtype,basedtype=basedtype,delim=delim,isJson=isJson):
                    _T_assertDataset(self,f"when setting the value of '{fq}'")
                    #_T_assertWritable(self,f"when setting the value of '{fq}'")
                    val=_cookValue(val,unit=unit,dtype=dtype,basedtype=basedtype,delim=delim)
                    # sys.stderr.write(f'{fq}: direct setting {val}\n')
                    if self.row is None: self.ctx.dataset[fq]=val
                    else: self.ctx.dataset[self.row,fq]=val
                def setter_wholeRow(self,val,*,fq=fq,unit=unit,dtype=dtype,basedtype=basedtype,delim=delim,isJson=isJson):
                    _T_assertDataset(self,f"when setting the value of '{fq}'")
                    #_T_assertWritable(self,f"when setting the value of '{fq}'")
                    val=_cookValue(val,unit=unit,dtype=dtype,basedtype=basedtype,delim=delim,isJson=isJson)
                    #sys.stderr.write(f'{fq}: wholeRow setting {repr(val)}\n')
                    # kind=='O' covers h5py.vlen_dtype and strings (h5py.string_dtype) with variable length
                    if self.row is None: raise NotImplementedError('Broadcasting to variable-length fields or multidimensional subarrays not yet implemented.')
                    setEntireDatasetRow_changeOneItem(ds=self.ctx.dataset,row=self.row,fq=fq,val=val)
                    #log.error(f'{rowdata=}')
                addAccessors(meth,key,getter,(setter_wholeRow if (dtype.kind=='O' or dtype.ndim>1) else setter_direct))
            elif 'schema' in val:
                schema,path=val['schema'],val.get('path','{NAME}/{ROW}/')
                path=path.replace('{NAME}',key)
                if '{ROW}' not in path: raise ValueError(f"'{fq}': schema ref path '{path}' does not contain '{{ROW}}'.")
                if not path.endswith('/'): raise ValueError(f"'{fq}': schema ref path '{path}' does not end with '/'.")
                ret.subpaths[fq]=(path,schema)
                # path=path[:-1] # remove trailing slash
                def subschemaGetter(self,row=None,*,fq=fq,path=path,schema=schema):
                    rr=[self.row is None,row is None]
                    if sum(rr)==2: raise AttributeError(f"'{fq}': row index not set (or given as arg), unable to follow schema ref.")
                    if sum(rr)==0: raise AttributeError(f"'{fq}': row given both as index ({self.row}) and arg ({row}).")
                    if row is None: row=self.row
                    #_T_assertDataset(self,f"when accessing subschema '{path}'.")
                    #self.ctx.dataset[self.row] # catch invalid row index, data unused
                    #print(f"{fq}: getting {path}")
                    path=path.replace('{ROW}',str(row))
                    subgrp=self.ctx.h5group.require_group(path)
                    SchemaT=self.ctx.schemaRegistry[schema]
                    ret=SchemaT(top=HeavyStruct.TopContext(h5group=subgrp,schemaRegistry=self.ctx.schemaRegistry,pyroIds=self.ctx.pyroIds),row=None)
                    # print(f"{fq}: schema is {SchemaT}, returning: {ret}.")
                    return _registeredWithDaemon(self,ret)
                ret.doc+=[docHead+': '+makeDoc(key,'nested data at `{path}`, schema `{schema}`.',ro=True)]
                addAccessors(meth,key,subschemaGetter)
            else:
                # recurse
                ret.doc+=[docHead+': '+makeDoc(key,doc='',ro=True)] # empty line for nesting in restructured text
                cooked=_cookSchema(val,prefix=fq,schemaName=schemaName,fakeModule=fakeModule,datasetName=datasetName,namingConvention=namingConvention)
                ret.append(cooked)
                def nestedGetter(self,*,T=cooked.T):
                    #print('nestedGetter',T)
                    ret=T(other=self)
                    return _registeredWithDaemon(self,ret)
                addAccessors(meth,key,nestedGetter)
        except BaseException as e:
            log.error(f'Error cooking {schemaName}, key {key}:')
            raise
    def _registeredWithDaemon(context,obj):
        if not hasattr(context,'_pyroDaemon'): return obj
        context._pyroDaemon.register(obj)
        context.ctx.pyroIds.append(obj._pyroId)
        return obj
    def T_init(self,*,top=None,other=None,row=None):
        '''
        The constructor is a bit hairy, as the new context either:
        (1) nests inside TopContext (think of dataset);
        (2) nests inside an already nested context (think of sub-dataset);
        (3) adds row information, not changing location (row in (sub)dataset)
        (4) nests & adds row, such as in getMolecules(0) which is a shorthand for getMolecules()[0]
        '''
        if top is not None:
            assert isinstance(top,HeavyStruct.TopContext)
            self.ctx,self.row=top,row
        elif other is not None:
            assert not isinstance(other,HeavyStruct.TopContext)
            # print(f'other.row={other.row}, row={row}')
            if (other.row is not None) and (row is not None): raise IndexError(f'Context already indexed, with row={row}.')
            self.ctx,self.row=other.ctx,(other.row if row is None else row)
           # print(f"[LEAF] {self}, other={other}")
        else: raise ValueError('One of *top* or *other* must be given.')
    def T_str(self):
        'Context string representation'
        return F"<{self.__class__.__name__}, row={self.row}, ctx={self.ctx}{', _pyroId='+self._pyroId if hasattr(self,'_pyroDaemon') else ''}>"
    def T_getitem(self,row):
        'Indexing access; checks index validity and returns new context with the row set'
        _T_assertDataset(self,msg=f'when trying to index row {row}')
        if(row<0 or row>=self.ctx.dataset.shape[0]): raise IndexError(f"{fq}: row index {row} out of range 0…{self.ctx.dataset.shape[0]}.")
        # self.ctx.dataset[row] # this would raise ValueError but iteration protocol needs IndexError
        # print(f'Item #{row}: returning {self.__class__(self,row=row)}')
        ret=self.__class__(other=self,row=row)
        return _registeredWithDaemon(self,ret)
        return ret
    def T_len(self):
        'Return sequence length'
        if not _T_hasDataset(self): return 0
        _T_assertDataset(self,msg=f'querying dataset length')
        if self.row is not None: return IndexError('Row index already set, not behaving as sequence.')
        return self.ctx.dataset.shape[0]
    def _T_hasDataset(self): return self.ctx.dataset or (self.__class__.datasetName in self.ctx.h5group)
    def _T_assertDataset(self,msg=''):
        'checks that the backing dataset it present/open. Raises exception otherwise.'
        if self.ctx.dataset is None:
            if self.__class__.datasetName in self.ctx.h5group: self.ctx.dataset=self.ctx.h5group[self.__class__.datasetName]
            else: raise RuntimeError(f'Dataset not yet initialized, use resize first{" ("+msg+")" if msg else ""}: {self.ctx.h5group.name}/{self.__class__.datasetName}.')
    def _T_assertWritable(self,msg):
        #log.error(f'{self.ctx.h5group.file=}')
        #log.error(f'{self.ctx.h5group.file.mode=}')
        if self.ctx.h5group.file.mode!='r+': raise RuntimeError(f'Underlying HDF5 file was not open for writing ({msg}).')
    def T_resize(self,size,reset=False,*,ret=ret):
        'Resizes the backing dataset; this will, as necessary, create a new dataset, or grow/shrink size of an existing dataset. New records are always default-initialized.'
        def _initrows(ds,rowmin,rowmax):
            'default-initialize contiguous range of rows rmin…rmax (inclusive), create groups for subpaths'
            defrow=ds[rowmin] # use first row as storage, assign all defaults into it, then copy over all other rows
            for fq,val in ret.defaults.items(): defrow[fq]=val
            ds[rowmin+1:rowmax+1]=defrow
        assert size>=0
        _T_assertWritable(self,msg=f'when resizing to {size}.')
        if reset: self.resize(size=0)
        if self.ctx.dataset is None:
            dsname=self.__class__.datasetName
            if dsname not in self.ctx.h5group: # create new dataset, initialize, return
                if size==0: return # request to reset but nothing is here
                self.ctx.dataset=self.ctx.h5group.create_dataset(dsname,shape=(size,),maxshape=(None,),dtype=ret.dtypes,compression='gzip')
                self.ctx.dataset.attrs['schema']=self.schemaName
                _initrows(ds=self.ctx.dataset,rowmin=0,rowmax=size-1)
                return
            else: # open existing dataset
                self.ctx.dataset=self.ctx.h5group[dsname]
        size0=self.ctx.dataset.shape[0]
        if size==size0: return
        self.ctx.dataset.resize((size,)) # this changes size of the underlying HDF5 data
        # default-initialize added rows
        if size0<size: _initrows(ds=self.ctx.dataset,rowmin=size0,rowmax=size-1)
        else:
            # remove stale subpaths
            # sys.stderr.write(f'Removing stale subpaths {str(ret.subpaths)}, {size0} → {size}…\n')
            for fq,(subpath,schema) in ret.subpaths.items():
                for r in range(size,size0):
                    p=subpath.replace('{ROW}',str(r))
                    # sys.stderr.write(f'Resizing {self.ctx.dataset}, {prevSize} → {size}: deleting {p}\n')
                    if p in self.ctx.h5group: del self.ctx.h5group[p]
                    else: pass # sys.stderr.write(f'{self.ctx.h5group}: does not contain {p}, not deleted')
    def T_inject(self,other):
        self.from_dump(other.to_dump())
    def T_to_dump(self,*,ret=ret):
        _T_assertDataset(self,msg=f'when dumping')
        def _onerow(row):
            d={'_schema':{"name":schemaName,"version":schemaVersion}}
            for fq,unit in ret.units.items(): #
                d[fq]=(self.ctx.dataset[row,fq],unit)
            for fq,(subpath,schema) in ret.subpaths.items():
                SchemaT=self.ctx.schemaRegistry[schema]
                subpath=subpath.replace('{ROW}',str(row))
                if subpath not in self.ctx.h5group: continue
                subgrp=self.ctx.h5group[subpath]
                subcontext=SchemaT(top=HeavyStruct.TopContext(h5group=subgrp,schemaRegistry=self.ctx.schemaRegistry,pyroIds=[]),row=None)
                d[fq]=subcontext.to_dump()
            return d
        if self.row is not None: return _onerow(self.row)
        else: return [_onerow(r) for r in range(self.ctx.dataset.shape[0])]
    def T_from_dump(self,dump,*,ret=ret):
        _T_assertWritable(self,msg=f'when applying dump')
        def _onerow(row,di):
            rowdata=self.ctx.dataset[row]
            s2n,s2v=di['_schema']['name'],di['_schema']['version']
            if s2n!=self.schemaName: raise ValueError(f'Schema mismatch: source {s2n}, target {self.schemaName}')
            if s2v!=self.schemaVersion: log.warning('Schema {s2n} version mismatch: source {s2v}, target {self.schemaVersion}')
            for fq,valUnit in di.items():
                if fq=='_schema': continue
                if fq in ret.units: # value field
                    rowdata[fq]=valUnit[0] if (valUnit[1] is None) else units.Quantity(value=valUnit[0],unit=valUnit[1]).to(ret.units[fq]).value
                elif fq in ret.subpaths: # subpath
                    assert isinstance(valUnit,list)
                    subpath,schema=ret.subpaths[fq]
                    SchemaT=self.ctx.schemaRegistry[schema]
                    subpath=subpath.replace('{ROW}',str(row))
                    subgrp=self.ctx.h5group.require_group(subpath)
                    subcontext=SchemaT(top=HeavyStruct.TopContext(h5group=subgrp,schemaRegistry=self.ctx.schemaRegistry,pyroIds=[]),row=None)
                    subcontext.from_dump(valUnit)
                else:
                    raise ValueError(f'Key {fq} not in target schema {self.schemaName}, in {self.ctx.h5group}.')
                    # key not in target schema
            self.ctx.dataset[row]=rowdata
        if self.row is not None:
            assert isinstance(dump,dict)
            _T_assertDataset(self,msg=f'when applying dump with row={self.row}')
            _onerow(self.row,dump)
        else:
            assert isinstance(dump,list)
            self.resize(len(dump),reset=True)
            _T_assertDataset(self,msg=f'when applying dump')
            for row,di in enumerate(dump): _onerow(row,di)

    def T_iter(self):
        _T_assertDataset(self,msg=f'when iterating')
        for row in range(self.ctx.dataset.shape[0]): yield self[row]

    meth['__init__']=T_init
    meth['__str__']=meth['__repr__']=T_str
    meth['__getitem__']=T_getitem
    meth['__len__']=T_len
    meth['row']=None
    meth['ctx']=None
    # __del__ note: it would be nice to use context destructor to unregister contexts from Pyro
    # (those which registered automatically). Since the daemon is holding one reference, however,
    # the dtor will never be called, unfortunately

    # those are defined only for the "root" context
    if not prefix:
        meth['resize']=T_resize
        meth['to_dump']=T_to_dump
        meth['from_dump']=T_from_dump
        meth['inject']=T_inject
        ret.dtypes=np.dtype(ret.dtypes)
        T_bases=()
    else:
        T_bases=() # only top-level has metadata

    T=type(T_name,T_bases,meth)
    T.__module__=fakeModule.__name__ ## make the (T.__module__,T.__name__) tuple used in serialization unique
    T.datasetName=datasetName
    T=Pyro5.api.expose(T)
    setattr(fakeModule,T_name,T)

    if not prefix:
        T.schemaName=schemaName # schema knows its own name, for convenience of creating schema registry
        T.schemaVersion=schemaVersion
        T.__doc__='\n'.join(ret.doc)+'\n'
        return T
    else:
        ret.T=T
        return ret


def makeSchemaRegistry(dd):
    '''
    Compile schema registry from dictionary representation; use ``json.loads`` to convert JSON schema to its dictionary representation.
    '''
    return dict([((T:=_cookSchema(d)).schemaName,T) for d in dd])


def _make_grains(h5name):
    import time, random
    from mupif.units import U as u
    t0=time.time()
    atomCounter=0
    # precompiled schemas
    schemaRegistry=makeSchemaRegistry(json.loads(sampleSchemas_json))
    with h5py.File(h5name,'w') as h5:
        grp=h5.require_group('test')
        schemaT=schemaRegistry['org.mupif.sample.grain']
        grp.attrs['schemas']=sampleSchemas_json
        grp.attrs['schema']=schemaT.schemaName
        grains=schemaT(top=HeavyStruct.TopContext(h5group=grp,schemaRegistry=schemaRegistry,pyroIds=[]))
        log.debug(f"{grains}")
        grains.resize(size=2)
        log.info(f"There is {len(grains)} grains.")
        for ig,g in enumerate(grains):
            #g=grains[ig]
            log.debug(f'grain {ig} {g}')
            g.getMolecules().resize(size=random.randint(5,20))
            log.debug(f"Grain #{ig} has {len(g.getMolecules())} molecules")
            for m in g.getMolecules():
                #for im in range(len(g.getMolecules())):
                #m=g.getMolecules()[im]
                # print('molecule: ',m)
                m.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
                m.getAtoms().resize(size=random.randint(30,60))
                for a in m.getAtoms():
                    #for ia in range(len(m.getAtoms())):
                    #a=m.getAtoms()[ia]
                    a.getIdentity().setElement(random.choice(['H','N','Cl','Na','Fe']))
                    a.getProperties().getTopology().setPosition((1,2,3)*u.nm)
                    a.getProperties().getTopology().setVelocity((24,5,77)*u.m/u.s)
                    # not yet, see https://stackoverflow.com/q/67192725/761090
                    struct=np.array([random.randint(1,20) for i in range(random.randint(5,20))],dtype='l')
                    a.getProperties().getTopology().setStructure(struct)
                    atomCounter+=1
    t1=time.time()
    log.info(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).')


def _read_grains(h5name):
    import time
    # note how this does NOT need any schemas defined, they are all pulled from the HDF5
    t0 = time.time()
    atomCounter = 0
    with h5py.File(h5name, 'r') as h5:
        grp = h5['test']
        schemaRegistry = makeSchemaRegistry(json.loads(grp.attrs['schemas']))
        grains = schemaRegistry[grp.attrs['schema']](top=HeavyStruct.TopContext(h5group=grp, schemaRegistry=schemaRegistry, pyroIds=[]))
        for g in grains:
            # print(g)
            log.info(f'Grain #{g.row} has {len(g.getMolecules())} molecules.')
            for m in g.getMolecules():
                m.getIdentity().getMolecularWeight()
                for a in m.getAtoms():
                    a.getIdentity().getElement()
                    a.getProperties().getTopology().getPosition()
                    a.getProperties().getTopology().getVelocity()
                    a.getProperties().getTopology().getStructure()
                    atomCounter += 1
    t1 = time.time()
    log.info(f'{atomCounter} atoms read in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).')


def HeavyDataHandle(*args, **kwargs):
    import warnings
    warnings.warn("HeavyDataHandle class was renamed to HeavyStruct, update your code.",DeprecationWarning)
    return HeavyStruct(*args, **kwargs)

@Pyro5.api.expose
class HeavyStruct(HeavyDataBase):
    h5group: str='/'
    schemaName: typing.Optional[str] = None
    schemasJson: typing.Optional[str] = None
    id: dataid.DataID = dataid.DataID.ID_None

    # __doc__ is a computed property which will add documentation for the sample JSON schemas
    __doc0__ = '''
Define semantic access to potentially large (that is, larger than RAM) structured data, both locally and over the network. The data structure is defined using *schemas* in JSON, where each schema defines table-like structure with rows of data, each row possibly further referencing another table with a different schema. The data is internally stored in a HDF5 file, which includes the schemas, making the file self-describing. JSON schema is thus only required when the data is being created, not for opening an already existing data.

*mode* specifies how the underlying HDF5 file (:obj:`h5path`) is to be opened:

* ``readonly`` only allows reading;
* ``readwrite`` alows reading and writing;
* ``create`` creates new HDF5 file, raising an exception if the file exists already; if :obj:`h5path` is empty, a temporary file will be created automatically; 
* ``overwrite`` create new HDF5 file, allowing overwriting an existing file;
* ``create-memory`` create HDF5 file in RAM only; if :obj:`h5path` is non-empty, it will be written out when data is closed via :obj:`closeData` (and discarded otherwise);

*schemaName* and *schemasJson* must be provided when creating new data (``overwrite``, ``create``, ``create-memory``) and are ignored otherwise.

This class can be used as context manager, in which case the :obj:`openData` and :obj:`closeData` will be called automatically.

**JSON schema specification**

The schema is defined as dictionary (nesting is possible). The top-level dictionary of each schema

#. **must** include ``_schema`` (which **must** define ``name`` and ``version``),
#. **must** include ``_datasetName`` entries,
#. **may** include other, regular entries, as described below; names **must not** be reserved names.

Reserved names are those starting with ``_`` (underscore) plus ``dtype``, ``lookup`` and ``path``.

* Regular entries

  Regular entries are one of the following.

  #. Computed attribute (identified via the ``lookup`` keyword); computed attribute **must** define ``lookup``, which is a lookup table (key-value dictionary), **dtype** (datatype being returned from lookup) and **key** (descriptor of data attribute used for lookup); it **may** define ``unit``.
  #. Data attribute (identified via the ``dtype`` key, but not having ``lookup``); it **must** define ``dtype`` and **may** define ``unit``, ``shape``.
  #. subschema reference (identified by the ``schema`` keyword); it **must** define ``schema`` (``path`` is optional).
  #. dictionary possibly including other regular entries (directory, creating hierarchy).

  * Data types

    ``dtype`` specifies datatype for the entry value using the ``numpy.dtype`` notation (see `Data type objects <https://numpy.org/doc/stable/reference/arrays.dtypes.html>`__), for example ``f8`` for 8-byte (64-bit) floating-point number.

    Strings are stored as utf-8 encoded byte arrays (thus their storage length might be larger than number of characters). use ``"dtype":"a"`` for variable-length strings (``a`` implies ``"shape":"variable"``), and ``"dtype":"a10"`` for string of maximum 10 bytes.

    String fields may specify *delim*, which is a delimiter sequence. The value will be presented as a tuple of strings to the user, interally stored as string joined by the *delim*. *delim* may be a single character or several characters. Values being set may not contain the delimiter itself. If the string is fixed-size, summary length of the string must not exceed the storage space. The value returned to the user is a tuple (read-only) to prevent in-place item modification.

    ``shape`` is a tuple specifying fixed shape: e.g. ``"shape":(3)`` is rank-1 3-vector, ``"shape":(3,3)`` is rank-2 3×3 matrix and so on. The special value of ``"shape":"variable"`` denotes dynamic 1d array of given ``dtype``.

    .. note:: Variable-length data (both strings and numerical arrays) are handled in a special way by the HDF5 storage; each (non-empty) entry has about 30b overhead, plus necessitates allocationes. If your data can always fit into a fixed-size array (such as string of maximum 20 bytes, ``a20``), prefer that for both performance ans storage reasons.

    All data are initialized to the default when constructed, which is:

    * ``NaN`` (not-a-number) for floating-point types (scalars and arrays),
    * ``0`` (zero) for integer types (scalars and arrays),
    * empty array for dynamic arrays,
    * empty string for both static-sized (``"dtype":"a10"``) and dynamic-sized (``"dtype":"a"``) strings.

    Assignments of incompatible data (which cannot be converted to the underlying storage type), including mismatched shape of arrays, will raise exception.

  * Units

    Entries specifying ``unit`` (which is any string `astropy.units.Unit <https://docs.astropy.org/en/stable/api/astropy.units.Unit.html>`__ can grok) **must** be assigned with quantities including compatible units; the value will be converted to the schema unit before being set. The field will be returned as a Quantity (including the unit) when read back.

  * Subschema

    Subschema entries associate full (nested hierarchical) data stratucture with each table line. The entry **must** specify ``schema`` name (which must be present in the *schemaRegistry* argument of :obj:`HeavyStruct.openData`). The ``path`` attribute is specified optionally (has a default value); path defines where the nested data is stored within the HDF5 file and **must** contain ``{ROW}`` (as string, including the curly braces) and end with ``/``.

**Accessing data**

Data are accesse using *Contexts*, special classes abstracting away the underlying storage. They define getters (and setters) for each data level (the are called simply ``get``/``set`` followed by capitalized entry name). Rows are selected using the usual indexing operator ``[index]``, though a whole column can be returned when index is not specified.

Top contexts (on the level of the schema) define a few special methods:

* ``resize`` which will change the number of rows; new rows will be always set to the default values. When passing the argument ``reset=True`` to ``resize``, all rows will be default-initialized.
* ``inject`` will replace the current context's data with data from another context (recursively); the routine will take care to resize structures as necessary. Schema names must be matching, and differences in schema versions will be reported as warning (it will be possible to user-define transformation for converting between different schema versions). The data exchange happens using serialized format which can be obtained and consumed using ``to_dump()`` and ``from_dump(…)`` methods.

Each parent group defines a special property ``schema_fragment`` which returns the schema as Python structure; this is to allow custom entries in the schema (such as descriptions or ontology mappings) to be accessed by the user.

    '''

    def getDataID(self):
        return self.id

    # from https://stackoverflow.com/a/3203659/761090
    class _classproperty(object):
        def __init__(self, getter): self.getter = getter
        def __get__(self, instance, owner): return self.getter(owner)

    @_classproperty
    def __doc__(cls):
        ret = cls.__doc0__
        reg = makeSchemaRegistry(json.loads(sampleSchemas_json))
        for key, val in reg.items():
            ret += '\n\n'+val.__doc__.replace('`', '``')
        return ret

    # this is not useful over Pyro (the Proxy defines its own context manager) but handy for local testing
    def __enter__(self): return self.openData(mode=self.mode)
    def __exit__(self, exc_type, exc_value, traceback): self.closeData()

    @dataclass
    @Pyro5.api.expose
    class TopContext:
        'This class is for internal use only. It is the return type of :obj:`HeavyStruct.openData` and others.'
        h5group: Any
        pyroIds: list
        schemaRegistry: dict
        dataset: Any = None

        def __str__(self):
            return f'{self.__module__}.{self.__class__.__name__}(h5group={str(self.h5group)},dataset={str(self.dataset)},schemaRegistry=<<{",".join(self.schemaRegistry.keys())}>>)'

    def __init__(self, **kw):
        super().__init__(**kw)

    @pydantic.validate_arguments
    def openData(self,mode=typing.Optional[HeavyDataBase_ModeChoice]):
        '''
        Return top context for the underlying HDF5 data. The context is automatically published through Pyro5 daemon, if the :obj:`HeavyStruct` instance is also published (this is true recursively, for all subcontexts). The contexts are unregistered when :obj:`HeavyStruct.closeData` is called (directly or via context manager).
        '''
        self.openStorage(mode=mode)
        extant=(self.h5group in self._h5obj and 'schema' in self._h5obj[self.h5group].attrs)
        if extant:
            # for modes readonly, readwrite
            grp = self._h5obj[self.h5group]
            schemaRegistry = makeSchemaRegistry(json.loads(grp.attrs['schemas']))
            top=schemaRegistry[grp.attrs['schema']](top=HeavyStruct.TopContext(h5group=grp, schemaRegistry=schemaRegistry, pyroIds=self.pyroIds))
            self.updateMetadata(json.loads(grp.attrs['metadata']))
            return self._returnProxy(top)
        else:
            if not self.schemaName or not self.schemasJson:
                raise ValueError(f'Both *schema* and *schemaJson* must be given (opening {self.h5path} in mode {self.mode})')
            # modes: overwrite, create, create-memory
            grp = self._h5obj.require_group(self.h5group)
            grp.attrs['schemas'] = self.schemasJson
            grp.attrs['schema'] = self.schemaName
            grp.attrs['metadata'] = json.dumps(self.getAllMetadata())
            schemaRegistry = makeSchemaRegistry(json.loads(self.schemasJson))
            top = schemaRegistry[grp.attrs['schema']](top=HeavyStruct.TopContext(h5group=grp, schemaRegistry=schemaRegistry, pyroIds=self.pyroIds))
            return self._returnProxy(top)
    def getSchemaName(self):
        self._ensureData()
        return self._h5obj[self.h5group].attrs['schema']
    def getSchemasJson(self):
        self._ensureData()
        return self._h5obj[self.h5group].attrs['schemas']


'''
future ideas:
* Create all context classes as Ctx_<md5 of the JSON schema> so that the name is unique.\
* Register classes to Pyro when the schema is read
* Register classes to remote Pyro when the heavy file is transferred?
'''

# uses relative imports, therefore run stand-alone as as:
#
# PYTHONPATH=.. python3 -m mupif.heavydata
#
if __name__ == '__main__':
    import json
    import pprint
    print(HeavyStruct.__doc__)
    # print(json.dumps(json.loads(sampleSchemas_json),indent=2))
    _make_grains('/tmp/grains.h5')
    _read_grains('/tmp/grains.h5')

    # this won't work through Pyro yet
    pp = HeavyStruct(h5path='/tmp/grains.h5', h5group='test')
    for key, val in pp.getSchemaRegistry(compile=True).items():
        print(val.__doc__.replace('`', '``'))
    grains = pp.openData('readonly')
    print(pp.openData(mode='readonly')[0].getMolecules())
    print(grains.getMolecules(0).getAtoms(5).getIdentity().getElement())
    print(grains[0].getMolecules()[5].getAtoms().getIdentity().getElement())
    import pprint
    mol5dump = grains[0].getMolecules()[5].to_dump()
    pp.closeData()
    grains = pp.openData('readwrite')
    grains[0].getMolecules()[4].from_dump(mol5dump)
    mol4dump = grains[0].getMolecules()[4].to_dump()
    # pprint.pprint(mol4dump)
    # pprint.pprint(mol4dump,stream=open('/tmp/m4.txt','w'))
    # pprint.pprint(mol5dump,stream=open('/tmp/m5.txt','w'))
    print(str(mol4dump) == str(mol5dump))
    pp.closeData()
