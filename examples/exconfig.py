# Common configuration for running examples in local, ssh or VPN mode
import sys
import os
import os.path
import Pyro5
import logging
import tempfile
import mupif.pyroutil
log = logging.getLogger()

allModes=[
    'localhost', # 0: 
    'ctu-ssh', # 1: ssh with real CTU IP addresses
    'vpn', # 2: vpn without ssh
    'wtf', # 3: "VPN emulated as local, no ssh tunnels" ?
    'local-noconf'
]

def getServerConfigMode():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-m','--mode',
        default='localhost',
        dest='mode',
        choices=allModes,
        help='Network mode for examples')
    return parser.parse_args().mode


class ExConfig(object):
    """
    Auxiliary class holding configuration variables for local, ssh, or VPN connection.
    Used mainly in mupif/examples/*
    Numerical value of parameter -m sets up internal variables.
    Typically, -m0 is local configuration, -m1 is ssh configuration, -m2 is VPN configuration, -m3 is VPN emulated as local
    """
    
    def __init__(self,*,mode=None):
        if mode is None: mode=getServerConfigMode()
        self.mode=mode

        #if mode not in [0, 1, 2, 3, 4]:
        #    log.error("Unknown mode -m %d" % mode)
        
        Pyro5.config.SERIALIZER = "serpent"
        # Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
        # Pyro5.config.SERIALIZERS_ACCEPTED = {'pickle'}
        Pyro5.config.SERVERTYPE = "multiplex"

        Pyro5.config.DETAILED_TRACEBACK=False
        sys.excepthook=Pyro5.errors.excepthook

        # commmon attributes
        # Password for accessing nameServer and applications
        # self.hkey = 'mupif-secret-key'
        Pyro5.config.SSL=False

        # Name of job manager
        self.jobManName = 'Mupif.JobManager@Example'
        # Name of first application
        self.appName = 'MuPIFServer'
        self.monitorName = 'monitor.MuPIF'

        # Jobs in JobManager
        # Range of ports to be assigned on the server to jobs
        self.portsForJobs = (9000, 9100)
        # NAT client ports used to establish ssh connections
        self.jobNatPorts = list(range(6000, 6100))

        # Maximum number of jobs
        self.maxJobs = 20
        # Auxiliary port used to communicate with application daemons on a local computer
        self.socketApps = 10000
        # Main directory for transmitting files

        # keep reference to the object around, the directory will be automatically deleted
        self.jobManWorkDirTemp=tempfile.TemporaryDirectory(prefix='jobman')
        self.jobManWorkDir = self.jobManWorkDirTemp.name # '.'

        self.jobMan2CmdPath=None
        
        #if 'TRAVIS' in os.environ:  # run everything locally on TRAVIS
        #    self.mode = 0
        
        if self.mode == 'localhost':  # localhost. Jobmanager uses NAT with ssh tunnels
            # NAME SERVER
            # IP/name of a name server
            self.nshost = '127.0.0.1'
            # self.nshost = '147.32.130.71'
            # Port of name server
            self.nsport = 9090

            self.monitorServer = '127.0.0.1'
            self.monitorPort = 9091

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

            # SECOND SERVER for another application on remote computer
            self.server2 = self.server
            self.serverPort2 = 44385
            self.serverNathost2 = self.server
            self.serverNatport2 = 5558
            self.appName2 = 'MuPIFServer2'

            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386
           
        elif self.mode == 'ctu-ssh':  # ssh
            # NAME SERVER
            # IP/name of a name server
            self.nshost = '147.32.130.71'
            # Port of name server
            self.nsport = 9090

            self.monitorServer = '127.0.0.1'
            self.monitorPort = 9091

            # SERVER for a single job or for JobManager
            # IP/name of a server's daemon
            self.server = '147.32.130.71'
            # Port of server's daemon
            self.serverPort = 44382
            # Nat IP/name (necessary for ssh tunnel)
            self.serverNathost = '127.0.0.1'
            # Nat port (necessary for ssh tunnel)
            self.serverNatport = 5555

            # SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44385
            self.serverNathost2 = self.server2
            self.serverNatport2 = 5558
            self.appName2 = 'MuPIFServer2'
        
        elif self.mode == 'vpn':  # VPN, no ssh tunnels
            # NAME SERVER
            # IP/name of a name server
            self.nshost = '172.30.0.1'
            # self.nshost = '172.30.0.6'
            # Port of name server
            self.nsport = 9090

            self.monitorServer = '172.30.0.1'
            self.monitorPort = 9091

            # SERVER for a single job or for JobManager
            # IP/name of a server's daemon
            # self.server = '172.30.0.1'
            self.server = '172.30.0.74'
            # Port of server's daemon
            self.serverPort = 44382
            # Nat IP/name
            self.serverNathost = None
            # Nat port
            self.serverNatport = None
            self.jobNatPorts = [None]

            # SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44383
            self.serverNathost2 = None
            self.serverNatport2 = None
            # self.appName2 = 'MuPIFServer2'
           
            # third SERVER - an application running on local computer in VPN
            # this server can be accessed only from script from the same computer
            # otherwise the server address has to be replaced by vpn local adress
            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386

        elif self.mode == 'wtf':  # VPN emulated as local, no ssh tunnels
            # NAME SERVER
            # IP/name of a name server
            self.nshost = '127.0.0.1'
            # Port of name server
            self.nsport = 9090

            self.monitorServer = '127.0.0.1'
            self.monitorPort = 9091

            # SERVER for a single job or for JobManager
            # IP/name of a server's daemon
            self.server = '127.0.0.1'
            # Port of server's daemon
            self.serverPort = 44382
            # Nat IP/name
            self.serverNathost = None
            # Nat port
            self.serverNatport = None
            self.jobNatPorts = [None]

            # SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44383
            # self.serverNathost2 = self.server2
            # self.serverNatport2 = 5558
            # self.appName2 = 'MuPIFServer2'
           
            # third SERVER - an application running on local computer in VPN
            # this server can be accessed only from script from the same computer
            # otherwise the server address has to be replaced by vpn local adress
            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386

        elif self.mode == 'local-noconf':
            ## docker-compose
            ## this is attempt at zero-config setup
            ## Pyro NS is located via broadcast and is used for looking up all the other components
            self.nshost='0.0.0.0'
            self.nsport=0
            self.monitorServer=None
            self.monitorPort=0
            self.server='0.0.0.0'
            self.serverPort=0
            self.serverNathost=None
            self.serverNatport=None
            self.jobNatPorts=[None]
            self.server2='0.0.0.0'
            self.serverPort2=0
            self.server3='0.0.0.0'
            self.serverPort3=0

        else: raise ValueError(f'Unhandled network mode "{mode}" for general setup (must be one of {", ".join(allModes)}).')

        self.sshHost = ''
        # SSH CLIENT
        # User name for ssh connection, empty uses current login name
        # serverUserName = os.environ.get( "USERNAME" )#current user-not working
        if self.mode in ('localhost','ctu-ssh'):
            thisdir = os.path.dirname(os.path.abspath(__file__))
            self.sshClient='asyncssh'
            self.options = f"-p2024 -N -F{os.devnull} -oIdentityFile={thisdir}/ssh/test_ssh_client_rsa_key " \
                           f"-oUserKnownHostsFile={thisdir}/ssh/test_ssh_client_known_hosts"
            # USERNAME is for win32
            self.serverUserName = os.environ.get('USER',os.environ.get('USERNAME'))
        elif self.mode in ('vpn','wtf','local-noconf'):  # VPN
            self.sshClient = 'manual'
            self.options = ''
        else: raise ValueError(f'Unhandled network mode "{mode}" for ssh setup: (must be one of {", ".join(allModes)}).')
