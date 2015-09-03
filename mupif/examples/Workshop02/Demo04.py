from __future__ import print_function
import sys
sys.path.append('../..')
import demoapp
import meshgen
from mupif import FieldID
from mupif import Field
from mupif import ValueType
from mupif import TimeStep
from mupif import PropertyID

app = demoapp.demoapp(None)
print(app.getApplicationSignature())

f = app.getField(FieldID.FID_Temperature, 0.0)

#two simple applications: minMax, integrate
app2 = demoapp.minMax()
app2.setField(f)
app2.solveStep(TimeStep.TimeStep(0.0, 1.0))
minimum = app2.getProperty(PropertyID.PID_Demo_Min, 0.0)
maximum = app2.getProperty(PropertyID.PID_Demo_Max, 0.0)
print ("field min = %f, max = %f" %(minimum.getValue()[0], maximum.getValue()[0]))

app3 = demoapp.integrateField()
app3.setField(f)
app3.solveStep(TimeStep.TimeStep(0,1))
val = app3.getProperty(PropertyID.PID_Demo_Integral, 0.0)
vol = app3.getProperty(PropertyID.PID_Demo_Volume, 0.0)
print ("field integral = %f, volume = %f" %(val.getValue(), vol.getValue()))
