# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../..', '../Example06-stacTM-local'])
from mupif import *

# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config

cfg = config(mode)

util.changeRootLogger('thermal.log')

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon for jobMamager on this machine
daemon = pyroutil.runDaemon(
    host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = simplejobmanager.SimpleJobManager2(
    daemon, ns, None, cfg.jobManName+'-ex08', cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', mode,
    cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

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



