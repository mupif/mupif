from . import apierror
from . import octree
from . import bbox
from . import baredata
from . import vertex
from . import cell
from . import units
from . import util
from . import localizer
from .mesh import Mesh

from .heavydata import HeavyConvertible
import copy
import time
import sys
import os.path
import numpy
import Pyro5
import dataclasses
import typing
from . import cellgeometrytype
import pickle
import deprecated
import numpy as np

import pydantic



@Pyro5.api.expose
class UniformRectilinearMesh(Mesh,HeavyConvertible):
    origin:  typing.Any=pydantic.Field(default_factory=lambda: np.array([1,1,1]))
    spacing: typing.Any=pydantic.Field(default_factory=lambda: np.array([1,1,1]))
    dims: typing.Any = None
    h5path: typing.Optional[str]=None
    h5group: typing.Optional[str]=None

    class GridLocalizer(localizer.Localizer):
        def __init__(self,grid,relPad=0):
            self.grid=grid
            self.pad=grid.spacing*relPad
        def getItemsInBBox(self,box):
            return self.grid.box_xyz2ijk(np.array(box.coords_ll)-self.pad,np.array(box.coords_ur)+self.pad);

    def is3d(self): return self.dims.shape[0]==3

    def getCellLocalizer(self):
        return UniformRectilinearMesh.GridLocalizer(self)

    @pydantic.model_validator(mode='before')
    @classmethod
    def convert_to_np_array(cls,vals):
        for f,dtype in [('origin','f'),('spacing','f'),('dims','i')]:
            if f in vals: vals[f]=np.array(vals[f],dtype=dtype)
        return vals

    def getNumberOfVertices(self):
        return np.prod(self.dims)
    def getNumberOfCells(self):
        return np.prod(self.dims-np.ones_like(self.dims))
    def getVertex(self, i):
        # assert self.dims.shape==(3,)
        return vertex.Vertex(number=i,coords=tuple(self.origin+self.i2ijk(i)*self.spacing))
    def box_xyz2ijk(self,xyz0,xyz1):
        dims_1=self.dims-np.ones_like(self.dims)
        ijk0=np.max([np.floor(np.divide(np.array(xyz0)-self.origin,self.spacing)).astype('int'),np.zeros_like(self.dims,dtype='int')],axis=0)
        ijk1=np.min([np.floor(np.divide(np.array(xyz1)-self.origin,self.spacing)+np.ones_like(self.dims)).astype('int'),dims_1],axis=0)
        ret=[]
        if self.is3d():
            for i in range(ijk0[0],ijk1[0]):
                for j in range(ijk0[1],ijk1[1]):
                    for k in range(ijk0[2],ijk1[2]):
                        ret.append(self.ijk2i((i,j,k),shrink=1))
                        #print(f'{i=} {j=} {k=} {self.getCell(I).getBBox()=}')
        else:
            for i in range(ijk0[0],ijk1[0]):
                for j in range(ijk0[1],ijk1[1]):
                    ret.append(I:=self.ijk2i((i,j),shrink=1))
        #print(f'{self.origin=} {self.spacing=} {self.dims=} {xyz0=} {xyz1=} {ijk0=} {ijk1=} {ret=}')
        return ret
    def i2ijk(self,i,shrink=0):
        dd=self.dims-shrink*np.ones_like(self.dims)
        if self.is3d():
            d01,d0=np.prod(dd[:2]),dd[0]
            return np.array([i%d0,(i%d01)//d0,i//d01]) # (i%d01)%d0=(i%(d0*d1))%d0=i%d0
        else:
            return np.array([i%dd[0],i//dd[0]])
    def ijk2i(self,ijk,shrink=0):
        dd=self.dims-shrink*np.ones_like(self.dims)
        if self.is3d():
            d01,d0=np.prod(dd[:2]),dd[0] 
            return int(ijk[0]+ijk[1]*d0+ijk[2]*d01)
        else:
            return int(ijk[0]+ijk[1]*dd[0])
    def getCell(self, i):
        d01,d0=np.prod(self.dims[:2]),self.dims[0]
        ijk=self.i2ijk(i,shrink=1)
        viA=self.ijk2i(ijk,shrink=0) # lowest-index vertex
        if self.is3d():
            viB=viA+d01
            vertices=(viA,viA+1,viA+d0+1,viA+d0,viB,viB+1,viB+d0+1,viB+d0)
            return cell.Brick_3d_lin(mesh=self,label=i,number=i,vertices=vertices)
        else:
            vertices=(viA,viA+1,viA+d0+1,viA+d0)
            return cell.Quad_2d_lin(mesh=self,label=i,number=i,vertices=vertices)
    def dataDigest(self) -> str:
        return util.sha1digest([self.origin,self.spacing,self.dims])
    def copyToHeavy(self,*,h5grp):
        mhash=self.dataDigest()
        if mhash in h5grp: return h5grp[mhash]
        gg=h5grp.create_group(name=mhash)
        gg.attrs['unit']=('' if self.unit is None else str(self.unit))
        gg.attrs['__class__']=self.__class__.__name__
        gg.attrs['__module__']=self.__class__.__module__
        gg['origin']=np.array(self.origin)
        gg['spacing']=np.array(self.spacing)
        gg['dims']=np.array(self.dims)
        return gg

    def asHdf5Object(self, parentgroup, heavyMesh=None):
        # heavyMesh ignored for UniformRectilinearMesh
        return self.copyToHeavy(h5grp=parentgroup)

    @classmethod
    def isHere(klass,*,h5grp):
        if '__class__' not in h5grp.attrs: return False
        if h5grp.attrs['__class__']!=klass.__name__: return False
        for ds in ['origin','spacing','dims']:
            if ds not in h5grp: raise IOError(f'Group {ds} missing (required for {klass.__name__}).')
        return True
    @classmethod
    def makeFromHdf5group(klass,h5grp):
        assert klass.isHere(h5grp=h5grp)
        return klass(origin=np.array(h5grp['origin']),spacing=np.array(h5grp['spacing']),dims=np.array(h5grp['dims']),h5path=h5grp.file.filename,h5group=h5grp.name)

    def writeXDMF(self,xdmf=None,fields=[],as3d=True):
        'Write crude XDMF file for inspection — without copying any of the heavy data.'
        if self.h5path is None: raise RuntimeError('This UniformRectilinearMesh was not loaded from a HDF5 file')
        if xdmf is None:
            xdmf=self.h5path+'.xdmf'
            xdmfH5path=os.path.basename(self.h5path)
        else:
            xdmfH5path=os.path.relpath(os.path.abspath(self.h5path),os.path.dirname(os.path.abspath(xdmf)))
        from xml.etree import ElementTree as ET
        def _E(tag,subs=[],text=None,**kw):
            ret=ET.Element(tag,**kw)
            if text: ret.text=text
            for s in subs: ret.append(s)
            return ret
        do3d=(self.is3d() or as3d)
        base=f'{xdmfH5path}:{self.h5group}'
        def arr2str(arr,extra):
            if len(arr)==2 and as3d: arr=np.hstack((arr,[extra]))
            return np.array2string(arr[::-1],separator=' ')[1:-1].strip()
        root=_E('Xdmf',Version="2.0",subs=[
            _E('Domain',[
                grid:=_E('Grid',GridType='Uniform',subs=[
                    _E('Topology',TopologyType=('3DCoRectMesh' if do3d else '2DCoRectMesh'),NumberOfElements=arr2str(self.dims,extra=1)),
                    _E('Geometry',GeometryType=('Origin_DxDyDz' if do3d else 'Origin_DxDy'),subs=[
                        _E('DataItem',Name='Origin',Dimensions=('3' if do3d else '2'),NumberType='Float',Precision='8',Format='XML',text=arr2str(self.origin,extra=0)),
                        _E('DataItem',Name=('DxDyDz' if do3d else 'DxDy'),Dimensions=('3' if do3d else '2'),NumberType='Float',Precision='8',Format='XML',text=arr2str(self.spacing,extra=1)),
                    ]),
                ])
            ])
        ])
        for field in fields:
            if id(field.mesh)!=id(self): raise ValueError('Field does not have this underlying mesh.')
            from .heavydata import Hdf5RefQuantity, Hdf5OwningRefQuantity
            from .field import FieldType
            from .mupifquantity import ValueType
            if not isinstance(field.quantity,(Hdf5RefQuantity,Hdf5OwningRefQuantity)): raise ValueError('Field not backed by HDF5 file?')
            name=field.getFieldIDName()
            xdmfH5path=os.path.relpath(os.path.abspath(field.quantity.dataset.file.filename),os.path.dirname(os.path.abspath(xdmf)))
            center={FieldType.FT_vertexBased:'Node',FieldType.FT_cellBased:'Cell'}[field.fieldType]
            attType={ValueType.Scalar:'Scalar',ValueType.Vector:'Vector',ValueType.Tensor:'Tensor'}[field.valueType]
            dim=' '.join([str(d-(0 if field.fieldType==FieldType.FT_vertexBased else 1)) for d in self.dims])
            if do3d and len(self.dims)==2: dim='1 '+dim
            if field.getRecordSize()>1: dim+=' '+str(field.getRecordSize())
            grid.append(_E('Attribute',Name=name,AttributeType=attType,Center=center,subs=[
                _E('DataItem',Dimensions=dim,NumberType='Float',Precision='8',Format='HDF',text=f'{xdmfH5path}:{field.quantity.dataset.name}_{3 if do3d else 2}d_view')
            ]))
        tree=ET.ElementTree(root)
        if hasattr(ET,'indent'): ET.indent(tree) # python >= 3.9
        tree.write(xdmf,xml_declaration=True,method='xml')

