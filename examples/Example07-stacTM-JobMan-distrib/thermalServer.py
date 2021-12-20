import sys
sys.path += ['..', '../..']
from exconfig import ExConfig
import models
import mupif as mp

cfg = ExConfig()

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=models.ThermalModel,
    appName='Mupif.JobManager@ThermalSolver-ex07',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
).runServer()
