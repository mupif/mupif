import sys
sys.path.append('../..')
import demoapp
import meshgen
from mupif import FieldID
from mupif import Field
from mupif import ValueType
from mupif import TimeStep
from mupif import PropertyID
from mupif import Mesh
from mupif import Vertex
from mupif import Cell

app = demoapp.thermal()
print app.getApplicationSignature()

f = app.getField(FieldID.FID_Temperature, 0.0)

#simple field mapping    
#mesh2 = meshgen.meshgen((0.0, 4.5), (10.0, 1.5), 50, 10);
mesh2 = meshgen.meshgen((0.0, 0.), (0.5, 0.3), 1, 1);



sol = app.solveStep(TimeStep.TimeStep(0,1)) 




values=[];
for i in mesh2.vertices():
    val = f.evaluate(i.getCoordinates())
    values.append(val)
f.field2VTKData().tofile('example2Orig')

#create new field on target mesh
f2=Field.Field(mesh2, FieldID.FID_Temperature, ValueType.Scalar, None, 0.0, values);
f2.field2VTKData().tofile('example2')
