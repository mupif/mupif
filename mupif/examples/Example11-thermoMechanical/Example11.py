from __future__ import print_function
import sys
sys.path.append('../../..')
sys.path.append('../Example10')
import demoapp
import meshgen
from mupif import *

if True:
    app = demoapp.thermal('inputT11.in','.')
    print(app.getApplicationSignature())

    sol = app.solveStep(TimeStep.TimeStep(0,1)) 
    f = app.getField(FieldID.FID_Temperature, 1.0)
    f.field2VTKData().tofile('thermal11')
    f.field2Image2D(title='Thermal', fileName='thermal.png')

if True:
    app2 = demoapp.mechanical('inputM11.in', '.')
    print(app2.getApplicationSignature())

    app2.setField(f)
    sol = app2.solveStep(TimeStep.TimeStep(0,1)) 
    f = app2.getField(FieldID.FID_Displacement, 1.0)
    f.field2VTKData().tofile('mechanical11')
    f.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')

#import time
#time.sleep(5)
