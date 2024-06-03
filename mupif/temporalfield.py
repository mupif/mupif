from .data import Data
from .field import Field, FieldType
from .units import Quantity
from .heavydata import HeavyDataBase
from .mesh import UnstructuredMesh
from .heavymesh import HeavyUnstructuredMesh
from .mupifquantity import ValueType
import pydantic
import astropy.units as au
import typing
import pickle
import Pyro5.api
import numpy as np
import os.path


class _FieldLocation(pydantic.BaseModel):
    field: str
    mesh: str


class _FieldMetadata(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    time: au.Quantity
    location: _FieldLocation
    user: dict = pydantic.Field(default_factory=dict)

    @pydantic.validator("time")
    def time_validator(cls, v):
        t = au.Unit(v)
        t.to(au.s)  # raises exception if not time dimension
        return t


@Pyro5.api.expose
class TemporalField(Data):
    fieldMeta: typing.List[_FieldMetadata] = []

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._cache={}
    def timeList(self) -> typing.List[Quantity]:
        return [md['time'] for md in self.fieldMeta]
    def timeMetadata(self, time, epsTime=0.0*au.s) -> dict:
        mmd=[md for md in self.fieldMeta if np.abs(md['time']-time)<=epsTime]
        if len(mmd)>=2: raise ValueError('Ambiguous time specification {time} with given eps={eps} ({len(mmd)} fields matching).')
        assert len(mmd)<2
        if len(mmd)==1: return mmd[0]
        return None
    def getField(self, time: Quantity, epsTime=0.0*au.s):
        # don't fetch field we already have
        if time in self._cache:
            return self._cache[time]
        # get metadata, raise exception if no data for given time
        md = self.timeMetadata(time)
        if md is None:
            raise ValueError(f'Field not defined for time {time}')
        # construct field from location
        self._cache[time] = self._field_make_from_loc(md['loc'])
        return self._cache[time]

    def getCachedTimes(self):
        return set(self._cache.keys())
    def evaluate(self,time: Quantity, positions, eps: float=0.0, epsTime=0.0*au.s):
        return self.getField(time,epsTime=epsTime).evaluate(positions=positions,eps=eps)
    def addField(self,field,userMetadata):
        time=field.getTime()
        if self.timeMetadata(time): raise ValueError(f'Field already saved for time {time}')
        loc=self._field_save_return_loc(field) # TODO: save userMetadata to the container redundantly
        self.fieldMeta.append({'time':time,'loc':loc,'user':userMetadata})
    def _field_make_from_loc(self,loc):
        fieldGrp,meshGrp=self._loc_to_h5_groups(loc)
        return Field.makeFromHdf5_groups(fieldGrp=fieldGrp,meshGrp=meshGrp,heavy=True)

class DirTemporalField(TemporalField):
    """Implementation of TemporalField which stored all data in local files"""
    dir: str

    def _loc_to_h5_groups(self, loc):
        import h5py
        return (
            h5py.File(f'{self.dir}/field/{loc["field"]}', 'r'),
            h5py.File(f'{self.dir}/mesh/{loc["mesh"]}', 'r')
        )

    def _field_save_return_loc(self, field):
        loc = field.toHdf5_split_files(fieldPrefix=f'{self.dir}/field/', meshPrefix=f'{self.dir}/mesh/', flat=True, heavy=True)
        return loc

class SingleFileTemporalField(TemporalField,HeavyDataBase):
    def __init__(self,*a,**kw):
        TemporalField.__init__(self,*a,**kw)
        HeavyDataBase.__init__(self,*a,**kw)
        self._cache={} # hack
    def _loc_to_h5_groups(self,loc):
        self._ensureData()
        return (self._h5obj[loc["field"]],self._h5obj[loc["mesh"]])
    def _field_save_return_loc(self,field):
        import h5py
        if not isinstance(field.getMesh(),UnstructuredMesh): raise RuntimeError('Field\'s mesh must be an UnstructuredMesh (not a {field.getMesh().__class__.__module__}.{field.getMesh().__class__.__name__}')
        mLoc='meshes/'+field.getMesh().dataDigest()
        fLoc='fields/'+field.dataDigest()
        if mLoc not in self._h5obj:
            # store as HeavyUnstructredMesh
            HeavyUnstructuredMesh.fromMeshioMesh_static(self._h5obj.create_group(mLoc),field.getMesh().toMeshioMesh())
        mg=self._h5obj[mLoc]
        fg=self._h5obj.create_group(fLoc)
        loc=field.toHdf5Group(fg,meshLink=h5py.SoftLink(mg.name))
        return {'field':fLoc,'mesh':mLoc}

    # this is not useful over Pyro (the Proxy defines its own context manager) but handy for local testing
    def __enter__(self):
        self.openData(mode=self.mode)
        return self
    def __exit__(self, exc_type, exc_value, traceback): self.closeData()
    def openData(self,mode=typing.Optional[HeavyDataBase.ModeChoice]):
        self.openStorage(mode=mode)
        if 'fields' in self._h5obj:
            for f in self._h5obj['fields']:
                grp=self._h5obj['fields'][f]
                print(f'{grp.name=}')
                self.fieldMeta.append({'time':pickle.loads(grp.attrs['time'].tobytes()),'loc':{'field':grp.name,'mesh':grp.name+'/mesh'}})
    def writeXdmf(self,xdmf=None,timeUnit=au.s):
        self._ensureData()
        from pathlib import Path
        if xdmf is None: xdmf=Path(self.h5path).with_suffix('.xdmf')
        h5=os.path.relpath(os.path.abspath(self.h5path),os.path.dirname(os.path.abspath(xdmf)))
        class Tag(object):
            def __init__(self,opening,closing,out): self.opening,self.closing,self.out=opening,closing,out
            def writeLn(self,s): self.out.write(self.out.level*'  '+s+'\n')
            def __enter__(self):
                self.writeLn(self.opening)
                self.out.level+=1
                return self
            def __exit__(self,exc_type,exc_value,traceback):
                self.out.level-=1
                self.writeLn(self.closing)
        out=open(xdmf,'wt')
        out.level=0
        with Tag('<?xml version="1.0" ?><Xdmf Version="3.0">','</Xdmf>',out):
            with Tag('<Domain>','</Domain>',out):
                with Tag('<Grid CollectionType="Temporal" GridType="Collection" Name="TimeSeries">','</Grid>',out):
                    for t in sorted(self.timeList()):
                        f=self.getField(time=t)
                        m=f.getMesh()
                        time=t.to(timeUnit)
                        with Tag(f'<Grid Name="Time {str(time)}">','</Grid>',out) as tag:
                            tag.writeLn(f'<Time Type="Single" Value="{time.value}"/>')
                            with Tag(f'<Geometry Type="{"XYZ" if m.dim==3 else "XY"}">','</Geometry>',out) as tag:
                                tag.writeLn(f'<DataItem DataType="Float" Dimensions="{m.getNumberOfVertices()} {m.dim}" Format="HDF" Precision="8">{h5}:{m.h5group}/{m.GRP_VERTS}</DataItem>')
                            with Tag(f'<Topology TopologyType="Mixed" NumberOfElements="{m.getNumberOfCells()}">','</Topology>',out) as tag:
                                tag.writeLn(f'<DataItem DataType="Int" Dimensions="{m._h5grp[m.GRP_CELL_CONN].shape[0]}" Format="HDF" Precision="8">{h5}:{m.h5group}/{m.GRP_CELL_CONN}</DataItem>')
                            attType={ValueType.Scalar:'Scalar',ValueType.Vector:'Vector',ValueType.Tensor:'Tensor'}[f.valueType]
                            center={FieldType.FT_vertexBased:'Node',FieldType.FT_cellBased:'Cell'}[f.fieldType]
                            dim=' '.join([str(i) for i in f.value.shape])
                            with Tag(f'<Attribute Name="{f.getFieldIDName()}" AttributeType="{attType}" Center="{center}">','</Attribute>',out) as tag:
                                tag.writeLn(f'<DataItem DataType="Float" Dimensions="{dim}" Format="HDF" Precision="8">{h5}:{f.quantity.dataset.name}</DataItem>')
        out.close()
        return xdmf


if 0:
    class HeavyStructTemporalField(TemporalField):
        """Implementation of TemporalField which puts data into HeavyStruct containers"""

        def _loc_to_h5_groups(self, loc):
            # zero-copy access: use underlying self._h5grp object of an already-open HDF5 group
            fieldGrp = self._h5grp['objects/'+loc['field']]
            meshGrp = self._h5grp['objects/'+loc['mesh']]
            return fieldGrp, meshGrp

        def _field_save_return_loc(self, field):
            meshDigest = field.mesh.internalArraysDigest()  # this is implemented already
            fieldDigest = field.internalArraysDigest()  # to be implemented for Field data
            field.toHdf5_split_groups(self._h5grp['objects/'+fieldDigest], self._h5grp['objecs/'+meshDigest])  # to be implemented in Field
            return {'field': fieldDigest, 'mesh': meshDigest}


#    class MongoTemporalField(TemporalField):
#        def _loc_to_h5_groups(self,loc):
#            import h5py
#            fieldHdf5=self.gridfs.fetch(loc['field'])
#            meshHdf5=self.gridfs.fetch(loc['mesh'])
#            return h5py.File(fieldHdf5,'ro')['field'],h5py.File(meshHdf5,'ro')['mesh']
#       def _field_save_return_loc(self,field):
#            field.toHdf5_split_files('field.h5','mesh.h5') # to be implemented in Field
#            fieldLoc=self._compute_digest('field.h5')
#            meshLoc=self._compute_digest('mesh.h5')
#            self.gridfs.store(src='field.h5',name=fieldLoc)
#            if self.grifs.find(meshLoc) is None: self.gridfs.store(src='mesh.h5',name=meshLoc)
#            return {'field':fieldLoc,'mesh':meshLoc}
#
