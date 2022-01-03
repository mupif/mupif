try:
    from .heavydata import HeavyDataBase, _HeavyDataBase_ModeChoice
    from .mesh import Mesh
    from .vertex import Vertex
    from .cell import Cell
    from . import cellgeometrytype as CGT
except ImportError:
    # for testing, when this file is run as script
    import mupif as mp
    from mupif import HeavyDataBase, Mesh, Vertex, Cell
    from mupif import cellgeometrytype as CGT
    from mupif.heavydata import _HeavyDataBase_ModeChoice

import Pyro5.api
import numpy as np
import os.path


@Pyro5.api.expose
class HeavyUnstructuredMesh(HeavyDataBase,Mesh):
    '''
    HDF5-backed unstructured mesh with mixed topology.

    Vertices and cells can be added to the mesh arbitrarily (grows dynamically).


    '''
    dim: int=3

    GRP_VERTS='vertices'
    GRP_CELL_OFFSETS='cellOffsets'
    GRP_CELL_CONN='connectivity'

    # see https://github.com/nschloe/meshio/blob/main/src/meshio/xdmf/common.py
    # and https://www.xdmf.org/index.php/XDMF_Model_and_Format#Arbitrary
    def __init__(self,*a,**kw):
        HeavyDataBase.__init__(self,*a,**kw)
        Mesh.__init__(self,*a,**kw)
        self._h5obj=None # this attribute is set in HeavyDataBase ctor but somehow does not survive... (is pydantic cleaning instance attributes? probably)
        self._h5grp=None
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
    def getCell(self,i):
        self._ensureData()
        if self.GRP_CELL_OFFSETS in self._h5grp: offset=self._h5grp[self.GRP_CELL_OFFSETS][i]
        else: raise RuntimeError('Reading from HDF5 without offset array not yet implemented.')
        cgt=CGT.xdmfIndex2cgt[self._h5grp[self.GRP_CELL_CONN][offset]]
        CellType=Cell.getClassForCellGeometryType(cgt)
        nVerts=CGT.cgt2numVerts[cgt]
        conn=self._h5grp[self.GRP_CELL_CONN][i+1:i+1+nVerts]
        return CellType(number=i,label=None,vertices=tuple(conn),mesh=self)

    def openData(self,mode: _HeavyDataBase_ModeChoice):
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
        self._ensureData()
        if coords.shape[1]!=self.dim: raise RuntimeError(f'Dimension mismatch: HeavyUnstructuredMesh.dim={self.dim}, coords.shape[1]={coords.shape[1]}.')
        _VERTS=self._h5grp[self.GRP_VERTS]
        l0,l1=_VERTS.shape[0],_VERTS.shape[0]+coords.shape[0]
        _VERTS.resize((l1,self.dim))
        self._h5grp[self.GRP_VERTS][l0:l1]=coords

    def appendCells(self,types,conn):
        _OFF,_CONN=self._h5grp[self.GRP_CELL_OFFSETS],self._h5grp[self.GRP_CELL_CONN]
        self._ensureData()
        assert len(types)==len(conn)
        if self.getNumberOfCells()==0: off=0
        else:
            lastOff=_OFF[self.getNumberOfCells()-1]
            lastLen=CGT.cgt2numVerts[_CONN[lastOff]]
            off=lastOff+lastLen+1
        # check number of vertices first
        for t,cc in zip(types,conn):
            if len(cc)!=CGT.cgt2numVerts[t]: raise RuntimeError(f'Cell of type {t} should have {CGT.cgt2numVerts[t]} vertices but {len(cc)} was given.')
        l0=_OFF.shape[0]
        # resize datasets
        _CONN.resize((_CONN.shape[0]+sum([len(cc)+1 for cc in conn]),))
        _OFF.resize((_OFF.shape[0]+len(types),))
        # assign data
        for i,(t,cc) in enumerate(zip(types,conn)):
            _OFF[l0+i]=off
            _CONN[off:off+1+len(cc)]=[CGT.cgt2xdmfIndex[t]]+list(cc)
            off+=len(cc)+1
    def writeXDMF(self):
        'Write crude XDMF file for inspection — without copying any of the heavy data.'
        base=f'{os.path.basename(self.h5path)}:{self.h5group}'
        open(self.h5path+'.xdmf','wb').write(f'''<?xml version="1.0"?>
<Xdmf Version="3.0">
  <Domain>
    <Grid Name="Grid">
      <Geometry GeometryType="{'XYZ' if self.dim==3 else 'XY'}">
        <DataItem DataType="Float" Dimensions="{self.getNumberOfVertices()} {self.dim}" Format="HDF" Precision="8">{base}/{self.GRP_VERTS}</DataItem>
      </Geometry>
      <Topology TopologyType="Mixed" NumberOfElements="{self.getNumberOfCells()}">
        <DataItem DataType="Int" Dimensions="13" Format="HDF" Precision="8">{base}/{self.GRP_CELL_CONN}</DataItem>
      </Topology>
    </Grid>
  </Domain>
</Xdmf>
'''.encode('utf-8'))

if __name__=='__main__':
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
    hum.openData(mode='create')
    hum.appendVertices(coords=verts)
    hum.appendCells(types=types,conn=conn)
    hum.closeData()

    hum.openData(mode='readonly')
    for i in range(hum.getNumberOfVertices()): print(hum.getVertex(i))
    for i in range(hum.getNumberOfCells()): print(hum.getCell(i))
    hum.writeXDMF()
    hum.closeData()

