from __future__ import print_function
import serverConfig as conf
from mupif import *
import DemoApplication

import logging
logger = logging.getLogger()

import Pyro4
import socket
import math
import os

#locate nameserver
ns = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible. Daemon registers SimpleJobManager2
try:
    daemon = Pyro4.Daemon(host=conf.daemonHost, port=conf.jobManPort, nathost=conf.nathost, natport=conf.jobManNatport) #, nathost="localhost", natport=6666)
except Exception as e:
    logger.debug('Daemon for JobManager can not start: host:%s, port:%d' % (conf.daemonHost, conf.jobManPort))
    logger.exception(e)
    exit(0)

jobMan = JobManager.SimpleJobManager2(daemon, ns, conf.applicationClass, "DemoApplication", conf.jobManPortsForJobs, conf.jobManWorkDir, os.getcwd(), 'serverConfig', conf.jobMan2CmdPath, conf.jobManMaxJobs, conf.jobManSocket) 
#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register(conf.jobManName, uri)
print ("Daemon for JobManager runs at " + str(uri))
print ("JobManager registered as " + conf.jobManName)
#waits for requests
daemon.requestLoop()
