# This script starts a server for Pyro4 on this machine with application2
# Works with Pyro4 version 4.54
# Tested on Ubuntu 16.04 and Win XP
# Vit Smilauer 03/2017, vit.smilauer (et) fsv.cvut.cz

# If firewall is blocking daemonPort, run on Ubuntu
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44382 -j ACCEPT

import sys
import logging
sys.path.extend(['.', '..', '../..'])
import mupif as mp
log = logging.getLogger()
mp.util.changeRootLogger('server.log')

from exconfig import ExConfig
cfg=ExConfig()

import application2
app2 = application2.Application2()

mp.pyroutil.runAppServer(
    server=cfg.server, port=cfg.serverPort,
    nshost=cfg.nshost, nsport=cfg.nsport,
    appName=cfg.appName,
    app=app2
)
