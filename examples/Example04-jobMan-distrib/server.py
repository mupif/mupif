import os
import sys
sys.path.extend(['..', '../..'])
import mupif as mp
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg=ExConfig()

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager2(
    daemon=None,
    ns=ns,
    appAPIClass=None,
    appName=cfg.jobManName,
    portRange=cfg.portsForJobs,
    jobManWorkDir=cfg.jobManWorkDir,
    serverConfigPath=os.getcwd(),
    serverConfigFile='serverConfig',
    serverConfigMode=cfg.mode,
    maxJobs=cfg.maxJobs,
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, nshost=cfg.nshost,
    nsport=cfg.nsport, appName=cfg.jobManName, jobman=jobMan, daemon=None
)
