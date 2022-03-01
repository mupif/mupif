import sys
sys.path += ['..', '../..']
import models
import mupif as mp

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=models.MechanicalModel,
    appName='Mupif.JobManager@MechanicalSolver-ex07',
).runServer()
