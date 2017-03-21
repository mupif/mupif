#Thermal server for nonstationary problem
from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import mupif
import demoapp
import conf_vpn as cfg

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

thermal = demoapp.thermal_nonstat('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputT13.in','.')
PyroUtil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.server, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, nsname='thermal', hkey=cfg.hkey, jobman=thermal)

#register agent
#uri = daemon.register(thermal)
#ns.register('thermal', uri)
#mupif.log.debug ("Daemon for thermal problem runs at " + str(uri))
#daemon.requestLoop()
