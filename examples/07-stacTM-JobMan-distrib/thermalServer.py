import sys
sys.path += ['..', '../..']
import mupif as mp

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.ThermalModel,
    appName='Mupif.JobManager@ThermalSolver-ex07',
).runServer()
