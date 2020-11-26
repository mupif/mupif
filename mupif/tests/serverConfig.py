# Configuration file for JobMan2cmd
import sys
import os
import os.path
import Pyro4
import logging
log = logging.getLogger()
import testApp




class serverConfig(object):
    """
    Auxiliary class holding configuration variables for local, ssh, or VPN connection.
    Used mainly in mupif/examples/*
    Numerical value of parameter -m sets up internal variables.
    Typically, -m0 is local configuration, -m1 is ssh configuration, -m2 is VPN configuration, -m3 is VPN emulated as local
    """
    
    def __init__(self, mode):
        Pyro4.config.SERIALIZER = "serpent"
        Pyro4.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
        Pyro4.config.SERIALIZERS_ACCEPTED = {'serpent'}
        Pyro4.config.SERVERTYPE = "multiplex"

        # Absolute path to mupif directory - used in JobMan2cmd
        mupif_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
        sys.path.append(mupif_dir)
            
        # Name of job manager
        self.jobManName = 'Mupif.JobManager@Example'
        # Name of first application
        self.appName = 'MuPIFServer'
        self.hkey = None

        # Jobs in JobManager
        # Range of ports to be assigned on the server to jobs
        self.portsForJobs = (9000, 9030)
    
        # Maximum number of jobs
        self.maxJobs = 20
        # Auxiliary port used to communicate with application daemons on a local computer
        self.socketApps = 10000
        # Main directory for transmitting files
        self.jobManWorkDir = '.'
        # Path to JobMan2cmd.py
        self.jobMan2CmdPath = "../tools/JobMan2cmd.py"
        
        
        # NAME SERVER
        # IP/name of a name server
        self.nshost = '127.0.0.1'
        # Port of name server
        self.nsport = 9092

        # SERVER for a single job or for JobManager
        # IP/name of a server's daemon
        self.server = '127.0.0.1'
        # self.server = '147.32.130.71'
        # Port of server's daemon
        self.serverPort = 44382
        # Nat IP/name (necessary for ssh tunnel)
        self.serverNathost = None
        # Nat port (necessary for ssh tunnel)
        self.serverNatport = None

        self.applicationClass = testApp.testApp
        self.applicationInitialFile = '/dev/null'  # dummy file

