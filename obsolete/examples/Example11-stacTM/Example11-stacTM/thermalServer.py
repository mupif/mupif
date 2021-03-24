import os,sys
sys.path.extend(['..','../../..','../Example10','../Example11-thermoMechanical'])#Path to demoapp
from mupif import *
import demoapp

## 1-Local setup - nameserver, thermal server, mechanical server, steering script.
## All runs on a local machine ##
#import conf as cfg


## 2-Distributed setup using VPN and peer-to-peer connection. Nameserver remote, thermal server remote.
## Mechanical server local, steering script local
#import conf_vpn as cfg

## 3-Distributed setup using VPN and jobManager connection. Nameserver remote, thermal server remote 
## via job Manager.
## Mechanical server local, steering script local
import conf_vpn as cfg

#locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon for jobManager on this machine
daemon = cfg.Pyro5.api.Daemon(host=cfg.server, port=cfg.serverPort)
#Run job manager on a server

#jobMan = simplejobmanager.SimpleJobManager(daemon, ns, appAPIClass=None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

pyroutil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.server, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, appName=cfg.jobManName, hkey=cfg.hkey, jobman=jobMan, daemon=daemon)
