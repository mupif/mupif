import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.MechanicalModel,
    appName='model',
).runServer()

