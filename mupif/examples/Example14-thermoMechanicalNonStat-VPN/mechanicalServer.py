#Mechanical server for nonstationary problem
from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import mupif
import demoapp
import conf_vpn as cfg
Util.changeRootLogger('mechanical.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

(user, hostname)=PyroUtil.getUserInfo()
mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputM13.in', '.')
PyroUtil.runAppServer(server=hostname, port=cfg.serverPort2, nathost=hostname, natport=cfg.serverPort2, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanical', hkey=cfg.hkey, app=mechanical)

