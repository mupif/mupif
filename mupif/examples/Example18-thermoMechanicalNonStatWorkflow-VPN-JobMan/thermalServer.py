from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import demoapp
import conf as cfg

Util.changeRootLogger('thermal.log')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
hkey = cfg.hkey #Password for accessing nameServer and applications
#Run a daemon for jobManager on this machine
daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort)

#Run job manager on a server
jobMan = SimpleJobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

PyroUtil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost='', natport='', nshost=cfg.nshost, nsport=cfg.nsport, appName=cfg.jobManName, hkey=cfg.hkey, jobman=jobMan, daemon=daemon)



