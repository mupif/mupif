from builtins import str

#import serverConfig as conf
import sys, os
#import common configuration file
sys.path.append('..')
import serverConfig as sConf

from mupif import *
import socket
import math
import logging
logger = logging.getLogger()

#locate nameserver
ns = pyroutil.connectNameServer(nshost=sConf.nshost, nsport=sConf.nsport, hkey=sConf.hkey)

#Run a daemon for JobManager. It will run even the port has DROP/REJECT status. The connection from a client is then impossible. Daemon registers SimpleJobManager
try:
    daemon = sConf.cfg.Pyro5.api.Daemon(host=sConf.server, port=sConf.jobManPort, nathost=sConf.serverNathost, natport=sConf.jobManNatport)
except Exception as e:
    logger.debug('Daemon for JobManager can not start: host:%s, port:%d' % (sConf.server, sConf.jobManPort))
    logger.exception(e)
    exit(0)

jobMan = JobManager.SimpleJobManager(daemon, ns, sConf.applicationClass, "DemoApplication", sConf.jobManPortsForJobs, sConf.jobManWorkDir, os.getcwd(), 'serverConfig', sConf.jobMan2CmdPath, sConf.jobManMaxJobs, sConf.jobManSocket) 
#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register(sConf.jobManName, uri)
logger.debug("Daemon for JobManager runs now (nat address) " + str(uri))
logger.debug("JobManager registered as " + sConf.jobManName)
#waits for requests
daemon.requestLoop()
