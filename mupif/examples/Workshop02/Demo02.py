from __future__ import print_function
import sys
sys.path.append('../..')
import demoapp
import meshgen

from mupif import FieldID
from mupif import Field

app = demoapp.demoapp(None)
print(app.getApplicationSignature())

f = app.getField(FieldID.FID_Temperature, 0.0)
print(f.evaluate((5.0, 5.0, 0.0)))

#get field evaluated outside domain -> error
#correct way
try:
    print(f.evaluate((5.0, -5.0, 0.0)))
except ValueError as e:
    print("Warning: point is outside the domain")
    print(0.0)


f.field2VTKData().tofile('example1')
