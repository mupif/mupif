import sys, time
sys.path.append('../..')
import meshgen
from mupif import *
import time
import logging
log = logging.getLogger()

mesh = mesh.UnstructuredMesh()
mesh = meshgen.meshgen((0., 0.), (3.2, 2.1), 5, 6, tria=False)
vert = mesh.getNumberOfVertices()
values = []
for i in range(vert):
    values.append( (i*0.5,i*1.5,i*2.5, i*0.5,0,i*0.5, -i*0.5,-i*1.5,-i*3.5 ) )

# Several units are predefined in physicalquantities, such as Pa and all prefixes
g = field.Field(mesh, DataID.FID_Stress, ValueType.Tensor, 'MPa', 0.0, values)

print( g.evaluate( (0.8, 2.0, 0) ) )
log.debug( g.evaluate( (0.8, 2.0, 0) ) )

g.field2VTKData().tofile('Tensors')
g.field2Image2D(title='Tensors', fileName='Tensors.png', fieldComponent=8)
time.sleep(5)

