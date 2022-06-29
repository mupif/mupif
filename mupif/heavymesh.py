from .heavydata import HeavyDataBase, HeavyDataBase_ModeChoice, Hdf5RefQuantity, Hdf5OwningRefQuantity
from .field import FieldType, Field
from .mupifquantity import ValueType
from .dataid import DataID
from .units import Unit, Quantity
from .cell import Cell
from .vertex import Vertex
from .mesh import Mesh
from .bbox import BBox
from . import octree
from . import cellgeometrytype as CGT
import logging
import Pyro5.api
import numpy as np
import os.path
from typing import ClassVar

log=logging.getLogger(__name__)


@Pyro5.api.expose
class HeavyUnstructuredMesh(HeavyDataBase,Mesh):
    '''
    HDF5-backed unstructured mesh with mixed topology.

    Vertices and cells can be added to the mesh arbitrarily (grows dynamically).
    '''
    dim: int=3
    h5group: str='/'

    GRP_VERTS: ClassVar[str]='mesh/vertices'
    GRP_CELL_OFFSETS: ClassVar[str]='mesh/cellOffsets'
    GRP_CELL_CONN: ClassVar[str]='mesh/connectivity'
    GRP_FIELDS: ClassVar[str]='fields'

    # see https://github.com/nschloe/meshio/blob/main/src/meshio/xdmf/common.py
    # and https://www.xdmf.org/index.php/XDMF_Model_and_Format#Arbitrary
    def __init__(self,*a,**kw):
        HeavyDataBase.__init__(self,*a,**kw)
        Mesh.__init__(self,*a,**kw)
        self._h5obj=None # this attribute is set in HeavyDataBase ctor but somehow does not survive... (is pydantic cleaning instance attributes? probably)
        self._h5grp=None


    # this is not useful over Pyro (the Proxy defines its own context manager) but handy for local testing
    def __enter__(self):
        self.openData(mode=self.mode)
        return self
    def __exit__(self, exc_type, exc_value, traceback): self.closeData()


    def _hasData(self):
        return hasattr(self,'_h5grp') and self._h5grp is not None
    def _ensureData(self):
        if not self._hasData(): raise RuntimeError('Backing storage (hdf5) not open yet.')
    def getNumberOfVertices(self):
        'Return number of vertices; returns -1 if backing storage is not open.'
        if not self._hasData(): return -1
        return self._h5grp[self.GRP_VERTS].shape[0]
    def getNumberOfCells(self):
        'Number of cells; returns -1 if backing storage is not open.'
        if not self._hasData(): return -1
        return self._h5grp[self.GRP_CELL_OFFSETS].shape[0]

    def getVertex(self,i):
        self._ensureData()
        return Vertex(number=i,label=None,coords=tuple(self._h5grp[self.GRP_VERTS][i]))
    def getGlobalBBox(self):
        self._ensureData()
        verts=self._h5grp[self.GRP_VERTS]
        mn,mx=np.min(verts,axis=0),np.max(verts,axis=0)
        return BBox(coords_ll=tuple(mn),coords_ur=tuple(mx))
    def getCell(self,i):
        self._ensureData()
        if self.GRP_CELL_OFFSETS in self._h5grp: offset=self._h5grp[self.GRP_CELL_OFFSETS][i]
        else: raise RuntimeError('Reading from HDF5 without offset array not yet implemented.')
        cgt=CGT.xdmfIndex2cgt[self._h5grp[self.GRP_CELL_CONN][offset]]
        CellType=Cell.getClassForCellGeometryType(cgt)
        nVerts=CGT.cgt2numVerts[cgt]
        conn=self._h5grp[self.GRP_CELL_CONN][offset+1:offset+1+nVerts]
        return CellType(number=i,label=None,vertices=tuple(conn),mesh=self)

    def getCellLocalizer(self):
        if self._cellOctree: return self._cellOctree
        bb=self.getGlobalBBox()
        # move all this to the octree ctor?
        minc, maxc = bb.coords_ll, bb.coords_ur
        size = max(y-x for x, y in zip(minc, maxc))
        mask = [(y-x) > 0.0 for x, y in zip(minc, maxc)]
        self._cellOctree = octree.Octree(minc, size, tuple(mask))
        verts=np.array(self._h5grp[self.GRP_VERTS])
        chunkSize=10000
        offGrp=self._h5grp[self.GRP_CELL_OFFSETS]
        import tqdm
        with tqdm.tqdm(total=offGrp.shape[0],unit=' cells',desc='octree') as pbar:
            for chunkStart in range(0,offGrp.shape[0],chunkSize):
                c0=offGrp[chunkStart]
                c1=(offGrp[chunkStart+chunkSize] if offGrp.shape[0]>chunkStart+chunkSize else None)
                dta=np.array(self._h5grp[self.GRP_CELL_CONN][c0:c1])
                self._cellOctree.insertCellArrayChunk(verts,dta,chunkStart,mesh=self)
                pbar.update(dta.shape[0])
        assert c1 is None # the last chunk must take the rest of the array
        return self._cellOctree


    def openData(self,mode: HeavyDataBase_ModeChoice):
        'Opens the backing storage (HDF5 file) and prepares'
        self.openStorage(mode=mode)
        extant=(self.h5group in self._h5obj and self.GRP_VERTS in self._h5obj[self.h5group])
        if not extant:
            self._h5grp=self._h5obj.require_group(self.h5group)
            kw=dict(chunks=True,compression='gzip',compression_opts=9)
            self._h5grp.create_dataset(self.GRP_VERTS,shape=(0,self.dim),maxshape=(None,self.dim),dtype='f8',**kw)
            self._h5grp.create_dataset(self.GRP_CELL_OFFSETS,shape=(0,),maxshape=(None,),dtype='i8',**kw)
            self._h5grp.create_dataset(self.GRP_CELL_CONN,shape=(0,),maxshape=(None,),dtype='i8',**kw)
        else:
            self._h5grp=self._h5obj[self.h5group]
        assert self.GRP_VERTS in self._h5grp
        assert self.GRP_CELL_CONN in self._h5grp
        assert self.GRP_CELL_OFFSETS in self._h5grp

    def appendVertices(self,coords: np.ndarray):
        'TODO: add to UnstructuredMesh API (and Mesh as abstract) as well'
        self._ensureData()
        # print('appendVertices coords: ',coords)
        if coords.shape[1]!=self.dim: raise RuntimeError(f'Dimension mismatch: HeavyUnstructuredMesh.dim={self.dim}, coords.shape[1]={coords.shape[1]}.')
        _VERTS=self._h5grp[self.GRP_VERTS]
        l0,l1=_VERTS.shape[0],_VERTS.shape[0]+coords.shape[0]
        _VERTS.resize((l1,self.dim))
        self._h5grp[self.GRP_VERTS][l0:l1]=coords

    def appendCells(self,types,conn):
        'TODO: add to UnstructuredMesh API (and Mesh as abstract) as well'
        _OFF,_CONN=self._h5grp[self.GRP_CELL_OFFSETS],self._h5grp[self.GRP_CELL_CONN]
        self._ensureData()
        assert len(types)==len(conn)
        if self.getNumberOfCells()==0: off=0
        else:
            lastOff=_OFF[self.getNumberOfCells()-1]
            # must convert xdmf cell type back to mupif cell type
            lastLen=1+CGT.cgt2numVerts[CGT.xdmfIndex2cgt[_CONN[lastOff]]]
            off=lastOff+lastLen
            # print(f'adding {len(types)} cells, offset is {off} (lastOff={lastOff},lastLen={lastLen})')
        # check number of vertices first
        for t,cc in zip(types,conn):
            if len(cc)!=CGT.cgt2numVerts[t]: raise RuntimeError(f'Cell of type {t} should have {CGT.cgt2numVerts[t]} vertices but {len(cc)} was given.')
        l0=_OFF.shape[0]
        # resize datasets
        dConn,dOff=sum([1+CGT.cgt2numVerts[t] for t in types]),len(types)
        # print(f'extending conn {_CONN.shape[0]} by {dConn}, offset {_OFF.shape[0]} by {dOff}')
        _CONN.resize((_CONN.shape[0]+dConn,))
        _OFF.resize((_OFF.shape[0]+dOff,))
        import sys
        # assign data
        for i,(t,cc) in enumerate(zip(types,conn)):
            _OFF[l0+i]=off
            _CONN[off:off+1+len(cc)]=[CGT.cgt2xdmfIndex[t]]+list(cc)
            #  sys.stderr.write(f'{len(cc)}')
            off+=len(cc)+1
            # sys.stdout.write(f'[{off};{off/9}]')
        # print(f'new offset is {off}, shape is {_CONN.shape}')
        assert off==_CONN.shape[0]
    def writeXDMF(self,xdmf=None,fields=[]):
        'Write crude XDMF file for inspection — without copying any of the heavy data.'
        if xdmf is None:
            xdmf=self.h5path+'.xdmf'
            xdmfH5path=os.path.basename(self.h5path)
        else:
            xdmfH5path=os.path.relpath(os.path.abspath(self.h5path),os.path.dirname(os.path.abspath(xdmf)))
        base=f'{xdmfH5path}:{self.h5group}'
        head=f'''<?xml version="1.0"?>
<Xdmf Version="3.0">
  <Domain>
    <Grid Name="Grid">
      <Geometry GeometryType="{'XYZ' if self.dim==3 else 'XY'}">
        <DataItem DataType="Float" Dimensions="{self.getNumberOfVertices()} {self.dim}" Format="HDF" Precision="8">{base}/{self.GRP_VERTS}</DataItem>
      </Geometry>
      <Topology TopologyType="Mixed" NumberOfElements="{self.getNumberOfCells()}">
        <DataItem DataType="Int" Dimensions="{self._h5grp[self.GRP_CELL_CONN].shape[0]}" Format="HDF" Precision="8">{base}/{self.GRP_CELL_CONN}</DataItem>
      </Topology>'''
        tail='''    </Grid>
  </Domain>
</Xdmf>
'''
        fieldXmls=[]
        for field in fields:
            if id(field.mesh)!=id(self): raise ValueError('Field does not have this underlying mesh.')
            name=field.getFieldIDName()
            xdmfH5path=os.path.relpath(os.path.abspath(field.quantity.dataset.file.filename),os.path.dirname(os.path.abspath(xdmf)))
            center={FieldType.FT_vertexBased:'Node',FieldType.FT_cellBased:'Cell'}[field.fieldType]
            attType={ValueType.Scalar:'Scalar',ValueType.Vector:'Vector',ValueType.Tensor:'Tensor'}[field.valueType]
            dim=' '.join([str(i) for i in field.value.shape])
            fieldXmls.append(f'''      <Attribute Name="{field.getFieldIDName()}" AttributeType="{attType}" Center="{center}">
        <DataItem DataType="Float" Dimensions="{dim}" Format="HDF" Precision="8">{xdmfH5path}:{field.quantity.dataset.name}</DataItem>
     </Attribute>''')
        open(xdmf,'wb').write('\n'.join([head]+fieldXmls+[tail]).encode('utf8'))
    def fromMeshioMesh(self,mesh,progress=False,chunk=10000):
        self._ensureData()
        # for now, don't allow adding mesh to an existing one
        # (it would be possible, only vertex number would have to be offset; usefulness = ?)
        assert self.getNumberOfVertices()==0
        assert self.getNumberOfCells()==0
        def seq(s,what):
            chunked=_chunker(s,chunk)
            if not progress: return chunked
            import tqdm, math, warnings
            warnings.simplefilter('ignore',tqdm.TqdmWarning)
            with tqdm.tqdm(total=len(s),unit=what,desc='meshio import') as pbar:
                for c in chunked:
                    yield c
                    pbar.update(len(c))
        for vv in seq(mesh.points,what=' verts'):
            self.appendVertices(coords=np.vstack(vv))
        for block in mesh.cells:
            cgt=CGT.meshioName2cgt[block.type]
            for cc in seq(block.data,what=' '+block.type):
                self.appendCells(types=len(cc)*[cgt],conn=cc)

    def makeHeavyField(self,*,fieldID,fieldType,valueType,unit,h5path='',dtype='f8',h5mode='create',fieldTime=0*Unit('s')):
        '''
        Create preallocated :obj:`mupif.Field` object storing its data in the same HDF5 file as the mesh (*self*). The field dimensions are determined from fieldType (cell/vertex based, plus the number of cells/vertices of the mesh object) and valueType (size of one record). The field's values are not assigned but allocated in the HDF5 container as a dataset.

        The usage looks as follows:

        >>> import mupif as mp
        >>> with mp.HeavyUnstructuredMesh(h5path='/tmp/t3.h5',mode='overwrite') as hMesh:
        >>>     # load mesh from somewhere
        >>>     hMesh.fromMeshioMesh(meshio.read('...'),progress=True,chunk=1000)
        >>>     # declare and allocate scalar field
        >>>     pressure=hMesh.makeHeavyField(unit='Pa',fieldID=mp.DataID.FID_Pressure,fieldType=mp.FieldType.FT_cellBased,valueType=mp.ValueType.Scalar)
        >>>     # fill field data
        >>>     pressure.value[:]=np.loadtxt('...',comments='%',usecols=(1,))
        >>>     # create vector field
        >>>     velocity=t3.makeHeavyField(unit='m/s',fieldID=mp.DataID.FID_Velocity,fieldType=mp.FieldType.FT_cellBased,valueType=mp.ValueType.Vector)
        >>>     velocity.value[:]=np.loadtxt('...',comments='%',usecols=(1,2,3))
        >>>     # write XDMF (can be opened in Paraview)
        >>>     t3.writeXDMF(xdmf='/tmp/t3.xdmf',fields=[pressure,velocity])


        '''
        n=(self.getNumberOfVertices() if fieldType==FieldType.FT_vertexBased else self.getNumberOfCells())
        if valueType.getNumberOfComponents()==1: shape=(n,)
        else: shape=(n,valueType.getNumberOfComponents())
        kw=dict(chunks=True,compression='gzip',compression_opts=9)
        if not h5path:
            ds=self._h5grp.create_dataset(self.GRP_FIELDS+'/'+fieldID.name,shape=shape,**kw)
            hq=Hdf5RefQuantity(dataset=ds,unit=unit)
        else:
            hq=Hdf5OwningRefQuantity(mode=h5mode,h5path=h5path,h5loc=self.GRP_FIELDS+'/'+fieldID.name,unit=unit)
            hq.allocateDataset(shape=shape,unit=unit,**kw)
        hq.dataset.attrs['fieldType']=fieldType.name
        hq.dataset.attrs['valueType']=valueType.name
        hq.dataset.attrs['time']=str(fieldTime)
        return Field(mesh=self,fieldType=fieldType,valueType=valueType,quantity=hq,fieldID=fieldID,time=fieldTime)
    @staticmethod
    def load(h5path,h5loc='/',open=True):
        import h5py
        h5=h5py.File(h5path,'r')
        base=h5[h5loc]
        for g in HeavyUnstructuredMesh.GRP_VERTS,HeavyUnstructuredMesh.GRP_CELL_OFFSETS,HeavyUnstructuredMesh.GRP_CELL_CONN:
            if g not in base: raise IOError(f'{h5path}::{h5loc}: {g} is missing')
        mesh=HeavyUnstructuredMesh(h5path=h5path,h5group=h5loc,mode='readonly')
        if open: mesh.openData(mode='readonly')
        if HeavyUnstructuredMesh.GRP_FIELDS not in base: return (mesh,[])
        fields=[]
        fieldsBase=base[HeavyUnstructuredMesh.GRP_FIELDS]
        for fName in fieldsBase:
            ds=fieldsBase[fName]
            log.error(f'Processing field {h5path}::{h5loc}/{HeavyUnstructuredMesh.GRP_FIELDS}/{fName} {ds.name}')
            fieldType=FieldType[ds.attrs['fieldType']]
            valueType=ValueType[ds.attrs['valueType']]
            time=Quantity(ds.attrs['time'])
            fieldID=DataID[fName]
            hq=Hdf5RefQuantity(dataset=ds)
            fields.append(Field(quantity=hq,mesh=mesh,fieldID=fieldID,fieldType=fieldType,valueType=valueType,time=time))
        return (mesh,fields)


def _chunker(it,size):
    rv = [] 
    for i,el in enumerate(it,1) :
        rv.append(el)
        if i % size == 0 :
            yield rv
            rv = []
    if rv : yield rv


if __name__=='__main__':
    # crude testing code, look away
    if 1:
        hum=HeavyUnstructuredMesh(h5path='/tmp/hum.h5')
        print(hum)
        verts=np.array([
            (0,0,0),
            (2,0,0),
            (0,5,0),
            (4,2,0),
            (5,4,0),
            (.5,5.5,0),
        ])
        types=[CGT.CGT_TRIANGLE_1,CGT.CGT_TRIANGLE_1,CGT.CGT_QUAD]
        conn=[(0,1,2),(1,2,3),(2,3,4,5)]
        hum.openData(mode='overwrite')
        hum.appendVertices(coords=verts)
        hum.appendCells(types=types,conn=conn)
        hum.closeData()

        hum.openData(mode='readonly')
        for i in range(hum.getNumberOfVertices()): print(hum.getVertex(i))
        for i in range(hum.getNumberOfCells()): print(hum.getCell(i))
        hum.writeXDMF()
        hum.closeData()

    if 0:
        # parse the Nastran BDF manually
        cells,verts=[],[]
        bdf=open('t-tmp/LC1-DR.geom.bdf','r')
        lineNo=-1
        while True:
            lineNo+=1
            l=bdf.readline()
            if len(l)==0: break
            l=l[:-1]
            if len(l)==0 or l[0]=='$': continue
            ll=l.split()
            if len(ll)==0:
                print(lineNo)
                continue
            # print(ll[0])
            if ll[0]=='CHEXA':
                ll+=bdf.readline().split()
                lineNo+=1
                assert len(ll)==11
                nn=[int(n) for n in ll[1:]]
                num,region,vv=nn[0],nn[1],[n-1 for n in nn[2:]] # nastran is 1-based for vertex numbers
                cells.append((CGT.CGT_HEXAHEDRON,vv))
            elif ll[0]=='GRID*':
                ll+=bdf.readline().split()
                lineNo+=1
                assert len(ll)==6
                #print(ll)
                n,xyz=int(ll[1]),(float(ll[2]),float(ll[3]),float(ll[5]))
                verts.append((n,xyz))
        if 0:
            import pprint
            pprint.pprint(cells)
            pprint.pprint(verts)
        print(f'Read {len(cells)} cells and {len(verts)} vertices.')
        def chunker(it,size):
            rv = [] 
            for i,el in enumerate(it,1) :
                rv.append(el)
                if i % size == 0 :
                    yield rv
                    rv = []
            if rv : yield rv
        t1=HeavyUnstructuredMesh(h5path='/tmp/t1.h5')
        t1.openData(mode='overwrite')
        chunk=10000
        print('Adding vertices')
        import tqdm
        with tqdm.tqdm(total=len(verts),unit=' verts') as pbar:
            for vv in chunker(verts,chunk):
                vv2=np.array([v[1] for v in vv])
                t1.appendVertices(coords=vv2)
                pbar.progress(len(vv))
        print('Adding cells')
        with tqdm.tqdm(total=len(cells),unit=' cells') as pbar:
            for cc in chunker(cells,chunk):
                t1.appendCells(types=[c[0] for c in cc],conn=[c[1] for c in cc])
                pbar.progress(len(cc))
        t1.writeXDMF()
        t1.closeData()
    if 1:
        # use meshio to load the bdf
        # must be "cleaned" (contain "BULK DATA"); continuation markers must be perhaps added, see https://github.com/nschloe/meshio/issues/1253
        import meshio
        mm=meshio.read('t-tmp/LC1-DR.geom.cleaned.2.bdf')
        with HeavyUnstructuredMesh(h5path='/tmp/t2.h5',mode='overwrite') as t2:
            t2.fromMeshioMesh(mm,progress=True,chunk=1000)
            t2.writeXDMF()
