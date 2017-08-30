#Mechanical server for nonstationary problem
import os,sys
sys.path.extend(['..','../../..','../Example10-stacTM-local'])
from mupif import *
import demoapp
Util.changeRootLogger('mechanical.log')
import Pyro4
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
#daemon = cfg.Pyro4.Daemon(host=cfg.server3, port=cfg.serverPort3)

mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-transiTM-local'+os.path.sep+'inputM13.in', '.')

#runs on local computer, no NAT
PyroUtil.runAppServer (server=cfg.server2, port=cfg.serverPort2, nathost=None, natport=None, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanical', hkey=cfg.hkey, app=mechanical)
