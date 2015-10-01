from __future__ import print_function
from builtins import str

#import serverConfig as conf
import sys, os
#import common configuration file
sys.path.append('..')
import conf as cfg
import serverConfig as sConf

from mupif import *
import socket
import math

logger = cfg.logging.getLogger()

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)

#Run a daemon for JobManager. It will run even the port has DROP/REJECT status. The connection from a client is then impossible. Daemon registers SimpleJobManager2
try:
    daemon = cfg.Pyro4.Daemon(host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)
except Exception as e:
    logger.debug('Daemon for JobManager can not start: host:%s, port:%d' % (cfg.server, cfg.serverPort))
    logger.exception(e)
    exit(0)

jobMan = JobManager.SimpleJobManager2(daemon, ns, sConf.applicationClass, "DemoApplication", cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'serverConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps) 
#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register(cfg.jobManName, uri)
logger.debug("Daemon for JobManager runs now (nat address) " + str(uri))
logger.debug("JobManager registered as " + cfg.jobManName)
#waits for requests
daemon.requestLoop()
