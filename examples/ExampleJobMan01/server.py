#Use on linux to reduce TIME_WAIT$  echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle

import conf
from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import FieldID
from mupif import Mesh
from mupif import Field
from mupif import ValueType
from mupif import Vertex
from mupif import Cell
from mupif import PyroUtil
from mupif import JobManager
import DemoApplication

import logging
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger()

import Pyro4
import socket
import math

#locate nameserver
ns = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible. Daemon registers SimpleJobManager2
try:
    daemon = Pyro4.Daemon(host=conf.daemonHost, port=conf.daemonPort) #, nathost="localhost", natport=6666)
except Exception as e:
    logger.debug('Daemon for JobManager can not start: host:%s, port:%d' % (conf.daemonHost, conf.daemonPort))
    logger.exception(e)
    exit(0)

jobMan = JobManager.SimpleJobManager2(daemon, ns, DemoApplication.DemoApplication, "DemoApplication", ( 9091, 9092, 9093, 9094), 2)
#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register("Mupif.JobManager@demo", uri)
print ("Daemon for JobManager runs at " + str(uri))
#waits for requests
daemon.requestLoop()
