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

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort)

thermal = demoapp.thermal_nonstat('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputT13.in','.')
#register agent
uri = daemon.register(thermal)
ns.register('thermal', uri)
mupif.log.debug ("Daemon for thermal problem runs at " + str(uri))
daemon.requestLoop()
