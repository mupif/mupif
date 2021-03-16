# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../..', '../Example06-stacTM-local'])
from mupif import *

from exconfig import ExConfig
cfg=ExConfig()

util.changeRootLogger('thermal.log')

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon for jobMamager on this machine
daemon = pyroutil.runDaemon(
    host=cfg.server, port=list(range(cfg.serverPort,cfg.serverPort+100)), nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = simplejobmanager.SimpleJobManager2(
    daemon=daemon, ns=ns, appAPIClass=None, appName=cfg.jobManName+'-ex08', portRange=cfg.portsForJobs, jobManWorkDir=cfg.jobManWorkDir, serverConfigPath=os.getcwd(), serverConfigFile='thermalServerConfig', serverConfigMode=cfg.mode,
    maxJobs=cfg.maxJobs)

pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nathost=None,
    natport=None,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName=cfg.jobManName+'-ex08',
    jobman=jobMan,
    daemon=daemon
)



