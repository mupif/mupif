import sys
sys.path.append('../..')

import logging
logging.basicConfig(filename='server.log',filemode='w',level=logging.DEBUG)
logger = logging.getLogger('server')
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
from mupif import PyroUtil
from mupif import JobManager

import PingServerApplication

import os


import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44361 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT


#locate nameserver
ns = PyroUtil.connectNameServer(nshost='147.32.130.137', nsport=9090, hkey=hkey)


#Run a daemon for jobMamager
daemon = PyroUtil.runDaemon(host='localhost', port=44361, nathost='localhost', natport=5555)
#Run job manager on a server
jobMan = JobManager.SimpleJobManager2(daemon, ns, PingServerApplication.PingServerApplication, "Mupif.PingServerApplication", ( 9091, 9092, 9093, 9094), 4)

#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register("Mupif.JobManager@demo", uri)
print ("Daemon for JobManager runs at " + str(uri))
#waits for requests
daemon.requestLoop()
