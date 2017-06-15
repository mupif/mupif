#Thermal server for nonstationary problem
from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import demoapp
import conf_vpn as cfg
Util.changeRootLogger('thermal.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

(user, hostname)=PyroUtil.getUserInfo()

thermal = demoapp.thermal_nonstat('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputT13.in','.')
PyroUtil.runAppServer(server=hostname, port=cfg.serverPort, nathost=hostname, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, appName='thermal', hkey=cfg.hkey, app=thermal)

#register agent
#uri = daemon.register(thermal)
#ns.register('thermal', uri)
#log.debug ("Daemon for thermal problem runs at " + str(uri))
#daemon.requestLoop()
