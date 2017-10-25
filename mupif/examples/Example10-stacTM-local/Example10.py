from __future__ import print_function
import sys
sys.path.append('../../..')
import demoapp
import meshgen
from mupif import *
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

if True:
    app = demoapp.thermal('inputT10.in','.')
    print(app.getApplicationSignature())

    sol = app.solveStep(TimeStep.TimeStep(0,1,1,timeUnits)) 
    f = app.getField(FieldID.FID_Temperature, 1.0)
    f.field2VTKData().tofile('thermal10')
    f.field2Image2D(title='Thermal', fileName='thermal.png')

if True:
    app2 = demoapp.mechanical('inputM10.in', '.')
    print(app2.getApplicationSignature())

    app2.setField(f)
    sol = app2.solveStep(TimeStep.TimeStep(0,1,1,timeUnits)) 
    f = app2.getField(FieldID.FID_Displacement, 1.0)
    f.field2VTKData().tofile('mechanical10')
    f.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')

log.info("Test OK")
