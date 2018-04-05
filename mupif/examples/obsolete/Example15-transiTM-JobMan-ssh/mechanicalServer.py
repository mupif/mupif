#Mechanical server for nonstationary problem
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import demoapp
import conf as cfg
Util.changeRootLogger('mechanical.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = cfg.Pyro4.Daemon(host=cfg.server2, port=cfg.serverPort2)

mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputM13.in', '.')
#register agent
uri = daemon.register(mechanical)
ns.register('mechanical', uri)
log.debug ("Daemon for mechanical problem runs at " + str(uri))
daemon.requestLoop()
