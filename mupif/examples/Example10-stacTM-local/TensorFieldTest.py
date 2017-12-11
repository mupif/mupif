import sys
sys.path.append('../../..')
import meshgen
from mupif import *
import time
import logging
log = logging.getLogger()


import mupif.Physics.PhysicalQuantities as PQ
stressUnits = PQ.PhysicalUnit('MPa',   1.,    [-1,1,-2,0,0,0,0,0,0])

mesh = Mesh.UnstructuredMesh()
mesh = meshgen.meshgen((0.,0.), (3.2, 2.1), 5, 6, tria=False) 
vert = mesh.getNumberOfVertices()
values = []
for i in range(vert):
    values.append( ((i*0.5,i*1.5,i*2.5), (i*0.5,0,i*0.5), (-i*0.5,-i*1.5,-i*3.5) ))

g = Field.Field(mesh, FieldID.FID_Stress, ValueType.Tensor, stressUnits, 0.0, values)
    
g.field2VTKData().tofile('Tensors')
g.field2Image2D(title='Tensors', fileName='Tensors.png', fieldComponent=8)
time.sleep(5)
