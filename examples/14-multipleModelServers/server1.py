import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

jobMan = mp.SimpleJobManager(
    ns = mp.pyroutil.connectNameserver(),
    appClass=mp.demo.ThermalModel,
    appName='model',
).runServer()
