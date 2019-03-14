import sys
sys.path.append('../../..')
import demoapp
import meshgen
from mupif import *
import time
import logging
log = logging.getLogger()


if True:
    app = demoapp.thermal()
    #app.printMetadata()
    app.initialize('inputT10.in','.')
    tstep = TimeStep.TimeStep(1.,1.,10,'s')
    sol = app.solveStep(tstep)
    print(app.printMetadata())
    f = app.getField(FieldID.FID_Temperature, app.getAssemblyTime(tstep))
    f.printMetadata()
    f.field2VTKData().tofile('thermal10')
    #f.field2Image2D(title='Thermal', fileName='thermal.png')
    time.sleep(1)
    valueT=f.evaluate((4.1, 0.9, 0.0))
    app.terminate()
    #app.printMetadata()
    #app.toJSON()
    #app.toJSONFile('aa.json')
    
    #print (valueT)



if True:
    app2 = demoapp.mechanical()
    app2.initialize('inputM10.in','.')
    print(app2.getApplicationSignature())

    app2.setField(f)
    sol = app2.solveStep(tstep) 
    f = app2.getField(FieldID.FID_Displacement, tstep.getTargetTime())
    f.field2VTKData().tofile('mechanical10')
    f.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')
    time.sleep(1)
    valueM=f.evaluate((4.1, 0.9, 0.0))
    app2.terminate()
    #app2.printMetadata()
    #print (valueM)

if ( (abs(valueT.getValue()[0]-5.1996464044328956) <= 1.e-8) and
    (abs(valueM.getValue()[1]-(-1.2033973431029044e-05)) <= 1.e-8) ):
    log.info("Test OK")
else:
    log.error("Test FAILED")
    print(valueT.getValue()[0], valueM.getValue()[1])
    sys.exit(1)

