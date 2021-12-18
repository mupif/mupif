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
    appClass=models.MechanicalModel,
    appName='Mupif.JobManager@MechanicalSolver-ex07',
    maxJobs=cfg.maxJobs,
    jobManWorkDir=cfg.jobManWorkDir
).runServer()
