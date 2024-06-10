import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns = mp.pyroutil.connectNameserver(),
    appClass=mp.demo.MechanicalModel,
    appName='model',
).runServer()

