import sys, os.path, os
d=os.path.dirname(os.path.abspath(__file__))
sys.path+=[d+'/..',d+'/../Example02-distrib',d+'../..']
import mupif as mp
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg=ExConfig()
import application2

# extend the configuration
cfg.applicationClass=application2.Application2

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager2(
    serverConfig=cfg,
    ns=ns,
    appName=cfg.jobManName,
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, nshost=cfg.nshost,
    nsport=cfg.nsport, appName=cfg.jobManName, jobman=jobMan, daemon=None
)
