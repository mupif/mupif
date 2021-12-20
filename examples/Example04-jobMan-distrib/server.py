import sys
import os
d=os.path.dirname(os.path.abspath(__file__))
sys.path += [d+'/..', d+'/../Example02-distrib', d+'/../..']
import mupif as mp
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg = ExConfig()
import application2

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=application2.Application2,
    appName=cfg.jobManName,
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
).runServer()
