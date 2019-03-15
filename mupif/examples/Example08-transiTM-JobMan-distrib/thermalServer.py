# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../../..', '../Example06-stacTM-local'])
from mupif import *
import demoapp
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config

cfg = config(mode)

Util.changeRootLogger('thermal.log')

# locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

# Run a daemon for jobMamager on this machine
daemon = PyroUtil.runDaemon(host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, hkey=cfg.hkey)

# Run job manager on a server
jobMan = SimpleJobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', mode, cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

PyroUtil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost=None, natport=None, nshost=cfg.nshost, nsport=cfg.nsport, appName=cfg.jobManName, hkey=cfg.hkey, jobman=jobMan, daemon=daemon)



