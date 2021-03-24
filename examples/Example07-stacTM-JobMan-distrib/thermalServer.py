import os, sys
sys.path+=['..']
from exconfig import ExConfig
import models
import mupif as mp

cfg=ExConfig()
cfg.applicationClass=models.ThermalModel

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    serverConfig=cfg,
    ns=ns,
    appName='Mupif.JobManager@ThermalSolver-ex07',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    # appName=cfg.jobManName+'-ex07',
    jobman=jobMan,
)
