#Mechanical server for nonstationary problem
import os,sys
sys.path.extend(['..', '../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)
import logging
log = logging.getLogger()
Util.changeRootLogger('mechanical.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
#daemon = PyroUtil.runDaemon(host=cfg.server3, port=cfg.serverPort3)

mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-transiTM-local'+os.path.sep+'inputM13.in', '.')

PyroUtil.runAppServer(server=cfg.server3, port=cfg.serverPort3, natport=None, nathost=None, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanical', hkey=cfg.hkey, app=mechanical)
