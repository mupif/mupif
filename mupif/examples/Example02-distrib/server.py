# This script starts a server for Pyro4 on this machine with application2
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 03/2017, vit.smilauer (et) fsv.cvut.cz

# If firewall is blocking daemonPort, run on Ubuntu
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44382 -j ACCEPT

import sys
import argparse
import logging
sys.path.extend(['..', '../../..'])
from mupif import *
log = logging.getLogger()
Util.changeRootLogger('server.log')

# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode

from Config import config

cfg = config(mode)

import application2
app2 = application2.application2()

PyroUtil.runAppServer(cfg.server, cfg.serverPort, cfg.serverNathost, cfg.serverNatport, cfg.nshost, cfg.nsport, cfg.appName, cfg.hkey, app=app2)
