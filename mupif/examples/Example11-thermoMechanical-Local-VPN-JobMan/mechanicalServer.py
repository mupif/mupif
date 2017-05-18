from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10','../Example11-thermoMechanical' ])#Path to demoapp
from mupif import *
import demoapp

## Local setup - nameserver, thermal server, mechanical server, steering script.
## All runs on a local machine ##
#import conf as cfg
#mechanical = demoapp.mechanical('inputM11.in', '.')
#log.info(mechanical.getApplicationSignature())
##locate nameserver and register application
#PyroUtil.runAppServer(server=cfg.server2, port=cfg.serverPort2, nathost=cfg.server2, natport=cfg.serverPort2, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanicalServer1', hkey=cfg.hkey, app=mechanical)


## Distributed setup using VPN and peer-to-peer connection. Nameserver remote, thermal server remote.
## Mechanical server local, steering script local
import conf_vpn as cfg
mechanical = demoapp.mechanical('inputM11.in', '.')
log.info(mechanical.getApplicationSignature())
#locate nameserver and register application
PyroUtil.runAppServer(server=cfg.server3, port=cfg.serverPort3, nathost=cfg.server3, natport=cfg.serverPort3, nshost=cfg.nshost, nsport=cfg.nsport, appName='mechanicalServer1', hkey=cfg.hkey, app=mechanical)







##Run a daemon for jobManager on this machine
#daemon = cfg.Pyro4.Daemon(host=127.0.0.1, port=44382)
##Run job manager on a server
#jobMan = JobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)
##set up daemon with JobManager
#uri = daemon.register(jobMan)
##register JobManager to nameServer
#ns.register(cfg.jobManName, uri)
#print ("Daemon for JobManager runs at " + str(uri))
##waits for requests
#daemon.requestLoop()
