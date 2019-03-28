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

Util.changeRootLogger('mechanical.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#(user, hostname)=PyroUtil.getUserInfo()

mechanical = demoapp.mechanical()
mechanical.initialize('..'+os.path.sep+'Example13-transiTM-local'+os.path.sep+'inputM13.in', '.')
PyroUtil.runAppServer(server=cfg.server, port=cfg.serverPort2, nathost=cfg.server, natport=cfg.serverPort2, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanical', hkey=cfg.hkey, app=mechanical)
