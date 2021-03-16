import os
import sys
sys.path.extend(['..', '../..'])
import mupif as mp
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg=ExConfig()

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
# Run a daemon for jobManager on this machine
daemon = mp.pyroutil.runDaemon(
    host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = mp.SimpleJobManager2(
    daemon=daemon,
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
    nsport=cfg.nsport, appName=cfg.jobManName, jobman=jobMan, daemon=daemon)
