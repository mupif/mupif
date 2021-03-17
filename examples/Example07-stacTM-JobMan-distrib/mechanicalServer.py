import os
import sys
sys.path.extend(['.','..', '../..'])
from mupif import *
util.changeRootLogger('mechanical.log')
import mechanicalServerConfig
cfg = mechanicalServerConfig.ServerConfig()

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon for jobMamager on this machine
#daemon = pyroutil.runDaemon(
#    host=cfg.server, port=list(range(cfg.serverPort,cfg.serverPort+100)), nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = simplejobmanager.SimpleJobManager2(
    daemon=None, ns=ns, appAPIClass=cfg.applicationClass, appName=cfg.jobManName+'-ex07', portRange=cfg.portsForJobs, jobManWorkDir=cfg.jobManWorkDir, serverConfigPath=os.getcwd(),
    serverConfigFile='mechanicalServerConfig', serverConfigMode=cfg.mode, maxJobs=cfg.maxJobs)

pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nathost=cfg.serverNathost,
    natport=cfg.serverNatport,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName=cfg.jobManName+'-ex07',
    jobman=jobMan,
    daemon=None
)
