# Mechanical server for nonstationary problem
import os
import sys
import logging
import argparse
sys.path.extend(['..', '../../..', '../Example06-stacTM-local'])
from mupif import *
import demoapp
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config

cfg = config(mode)
log = logging.getLogger()
Util.changeRootLogger('mechanical.log')

# locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

# Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
# daemon = PyroUtil.runDaemon(host=cfg.server3, port=cfg.serverPort3)

mechanical = demoapp.mechanical()
# mechanical.initialize('..'+os.path.sep+'Example06-stacTM-local'+os.path.sep+'inputM10.in', '.')

PyroUtil.runAppServer(
    server=cfg.server3,
    port=cfg.serverPort3,
    natport=None,
    nathost=None,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName='mechanical',
    hkey=cfg.hkey,
    app=mechanical
)
