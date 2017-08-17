from __future__ import print_function
import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import mupif
import demoapp
import conf as cfg
Util.changeRootLogger('thermal.log')

#if you wish to run no SSH tunnels, set to True
noSSH=False

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

if noSSH:
    cfg.server = cfg.serverNathost
    cfg.jobManNatport = cfg.jobManPort

#Run a daemon for jobManager on this machine
daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)
#Run job manager on a server
#thermalApp = demoapp.thermal_nonstat('..'+os.path.sep+'Example13-thermoMechanicalNonStat'+os.path.sep+'inputT13.in','.')
jobMan = JobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register(cfg.jobManName, uri)
print ("Daemon for JobManager runs at " + str(uri))
#waits for requests
daemon.requestLoop()
