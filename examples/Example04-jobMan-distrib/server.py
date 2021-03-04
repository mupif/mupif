import os
import sys
sys.path.extend(['..', '../..'])
import mupif as mp
mp.util.changeRootLogger('server.log')
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[mp.util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)

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
    serverConfigMode=mode,
    jobMan2CmdPath=cfg.jobMan2CmdPath,
    maxJobs=cfg.maxJobs,
    jobMancmdCommPort=cfg.socketApps
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, nshost=cfg.nshost,
    nsport=cfg.nsport, appName=cfg.jobManName, jobman=jobMan, daemon=daemon)
