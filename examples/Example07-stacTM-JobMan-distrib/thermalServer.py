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
    appClass=models.ThermalModel,
    #server=cfg.server,
    ns=ns,
    appName='Mupif.JobManager@ThermalSolver-ex07',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    ns=ns,
    #server=cfg.server,
    #port=cfg.serverPort,
    #nshost=cfg.nshost,
    #nsport=cfg.nsport,
    # appName=cfg.jobManName+'-ex07',
    jobman=jobMan,
)
