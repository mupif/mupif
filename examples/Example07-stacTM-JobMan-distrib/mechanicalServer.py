import os
import sys
sys.path+=['..']
import mupif as mp


from exconfig import ExConfig
cfg=ExConfig()
import models

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    appClass=models.MechanicalModel,
    server=cfg.server,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    ns=ns,
    appName='Mupif.JobManager@MechanicalSolver-ex07',
    maxJobs=cfg.maxJobs,
    jobManWorkDir=cfg.jobManWorkDir
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort+1,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    # appName=cfg.jobManName+'-ex07',
    jobman=jobMan,
)
