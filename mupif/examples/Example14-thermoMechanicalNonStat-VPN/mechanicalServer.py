#Mechanical server for nonstationary problem
from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import mupif
import demoapp
import conf_vpn as cfg

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputM13.in', '.')
PyroUtil.runAppServer(server=cfg.server2, port=cfg.serverPort2, nathost=cfg.server2, natport=cfg.serverPort2, nshost=cfg.nshost, nsport=cfg.nsport, nsname='mechanical', hkey=cfg.hkey, jobman=mechanical)

