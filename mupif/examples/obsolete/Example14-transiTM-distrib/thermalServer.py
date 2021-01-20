#Thermal server for nonstationary problem
import os,sys
sys.path.extend(['..', '../../..', '../Example10-stacTM-local'])
from mupif import *
import demoapp
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)

util.changeRootLogger('thermal.log')

#locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#(user, hostname)=pyroutil.getUserInfo()

thermal = demoapp.thermal_nonstat()
thermal.initialize('..'+os.path.sep+'Example13-transiTM-local'+os.path.sep+'inputT13.in','.')

pyroutil.runAppServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, nshost=cfg.nshost, nsport=cfg.nsport, appName='thermal', hkey=cfg.hkey, app=thermal)
