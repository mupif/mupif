#Mechanical server for nonstationary problem
from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import demoapp
import conf as cfg

Util.changeRootLogger('mechanical.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
#daemon = cfg.Pyro4.Daemon(host=cfg.server3, port=cfg.serverPort3)

mechanical = demoapp.mechanical('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputM13.in', '.')


PyroUtil.runAppServer (server=cfg.server3, port=cfg.serverPort3, natport='', nathost='',
                       nshost=cfg.nshost, nsport=cfg.nsport,
                       appName='mechanical', hkey=cfg.hkey, app=mechanical)


#register agent
#uri = daemon.register(mechanical)
#ns.register('mechanical', uri)
#log.debug ("Daemon for mechanical problem runs at " + str(uri))
#daemon.requestLoop()
