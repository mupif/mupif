from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10','../Example11-thermoMechanical'])#Path to demoapp
from mupif import *
import demoapp

#python jobManStatus.py -n 172.30.0.1 -r 9090 -h 172.30.0.1 -p 44382 -j 'jobMan1' -k 'mupif-secret-key'

## 1-Local setup - nameserver, thermal server, mechanical server, steering script.
## All runs on a local machine ##
#import conf as cfg


## 2-Distributed setup using VPN and peer-to-peer connection. Nameserver remote, thermal server remote.
## Mechanical server local, steering script local
#import conf_vpn as cfg

###Common part for 1 or 2
#thermal = demoapp.thermal('inputT11.in','.')
#log.info(thermal.getApplicationSignature())
##locate nameserver and register thermal application
#PyroUtil.runAppServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.server, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, nsname='thermalServer1', hkey=cfg.hkey, app=thermal)



## 3-Distributed setup using VPN and jobManager connection. Nameserver remote, thermal server remote 
## via job Manager.
## Mechanical server local, steering script local
import conf_vpn as cfg

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon for jobManager on this machine
daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort)
#Run job manager on a server

jobMan = JobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

PyroUtil.runAppServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.server, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, nsname='jobMan1', hkey=cfg.hkey, app=jobMan, daemon=daemon , metadata={PyroUtil.NS_METADATA_jobmanager})

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
