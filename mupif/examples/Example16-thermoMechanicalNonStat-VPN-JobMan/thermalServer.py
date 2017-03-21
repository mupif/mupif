from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import mupif
import demoapp
import conf_vpn as cfg

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon for jobManager on this machine
daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort)

#Run job manager on a server
jobMan = JobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

PyroUtil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost=cfg.server, natport=cfg.serverPort, nshost=cfg.nshost, nsport=cfg.nsport, 
                             nsname=cfg.jobManName, hkey=cfg.hkey, jobman=jobMan, daemon=daemon)



