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

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = Pyro4.Daemon(host=conf.daemonHost, port=conf.daemonPort) #, nathost="localhost", natport=6666)

jobMan = JobManager.SimpleJobManager2(daemon, ns, DemoApplication.DemoApplication, "DemoApplication", (9090, 9091, 9092, 9093, 9094, 9095, 9096, 9097, 9098, 9099), 4)
#register agent
uri    = daemon.register(jobMan)
ns.register("Mupif.JobManager@demo", uri)
print (uri)
daemon.requestLoop()
