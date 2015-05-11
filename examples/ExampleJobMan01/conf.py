#where is a running nameserver
nshost = "ksm.fsv.cvut.cz"
nsport = 9090
#address where JobManager will listen through a daemon
#daemonHost = "jaja.fsv.cvut.cz"
#daemonPort = 44382
#address where this server will listen through a daemon
daemonHost = "localhost"
daemonPort = 44382

import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 
os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
Pyro4.config.AUTOPROXY=False
Pyro4.config.COMMTIMEOUT = 10.0 #network communication timeout in seconds.
#Pyro4.config.SOCK_REUSE = True #can use occupied port. This will not work for the ssh tunnel, which needs a free port to bind to.

from mupif import PyroUtil #get the logging

import logging
logger = logging.getLogger()

import DemoApplication
appClass = DemoApplication.DemoApplication


