# Common configuration for running examples in local, ssh or VPN mode
import sys
import os
import os.path
import Pyro5
import logging
import tempfile
# for mupif itself
thisDir = os.path.dirname(os.path.abspath(__file__))
sys.path += [thisDir+'/..']

import mupif

log = logging.getLogger()

allModes = [
    'localhost',  # 0:
    'ctu-ssh',  # 1: ssh with real CTU IP addresses
    'vpn',  # 2: vpn without ssh
    'wtf',  # 3: "VPN emulated as local, no ssh tunnels" ?
    'local-noconf'
]


def getServerConfigMode():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-m', '--mode',
        default='localhost',
        dest='mode',
        choices=allModes,
        help='Network mode for examples'
    )
    return parser.parse_args().mode


class ExConfig(object):
    """
    Auxiliary class holding configuration variables for local, ssh, or VPN connection.
    Used mainly in mupif/examples/*
    Numerical value of parameter -m sets up internal variables.
    Typically, -m0 is local configuration, -m1 is ssh configuration, -m2 is VPN configuration, -m3 is VPN emulated as local
    """
    
    def __init__(self, *, mode=None):
        if mode is None:
            mode = getServerConfigMode()
        self.mode = mode

        # if mode not in [0, 1, 2, 3, 4]:
        #     log.error("Unknown mode -m %d" % mode)
        
        Pyro5.config.SERIALIZER = "serpent"
        # Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # to work with python 2.x and 3.x
        # Pyro5.config.SERIALIZERS_ACCEPTED = {'pickle'}
        Pyro5.config.SERVERTYPE = "multiplex"

        Pyro5.config.DETAILED_TRACEBACK = False
        sys.excepthook = Pyro5.errors.excepthook

        # commmon attributes
        Pyro5.config.SSL = False

        # Name of job manager
        self.jobManName = 'Mupif.JobManager@Example'
        # Name of first application
        self.appName = 'MuPIFServer'
        self.appName2 = 'MuPIFServer2'
        self.monitorName = 'monitor.MuPIF'

        # Maximum number of jobs
        self.maxJobs = 20

        # keep reference to the object around, the directory will be automatically deleted
        self.jobManWorkDirTemp = tempfile.TemporaryDirectory(prefix='mupif-')
        self.jobManWorkDir = self.jobManWorkDirTemp.name  # '.'

        self.jobMan2CmdPath = None
        
        # if 'TRAVIS' in os.environ:  # run everything locally on TRAVIS
        #    self.mode = 0
        
        if self.mode == 'localhost':  # localhost. Jobmanager uses NAT with ssh tunnels
            self.nshost = self.server = self.server2 = self.server3 = self.monitorServer = '127.0.0.1'
            self.nsport = 9090
            self.monitorPort = 9091
            self.serverPort = 44382
            self.serverPort2 = 44385
            self.serverPort3 = 44386

        elif self.mode == 'local-noconf':
            # docker-compose
            # this is attempt at zero-config setup
            # Pyro NS is located via broadcast and is used for looking up all the other components
            self.nshost = self.server = self.server2 = self.server3 = '0.0.0.0'
            self.nsport = self.monitorPort = self.serverPort = self.serverPort2 = self.serverPort3 = 0
            self.monitorServer = None

        else:
            raise ValueError(f'Unhandled network mode "{mode}" for general setup (must be one of {", ".join(allModes)}).')

        self.sshHost = ''
        # SSH CLIENT
        # User name for ssh connection, empty uses current login name
        # serverUserName = os.environ.get( "USERNAME" )#current user-not working
        if self.mode in ('localhost', 'ctu-ssh'):
            thisdir = os.path.dirname(os.path.abspath(__file__))
            self.sshClient = 'asyncssh'
            self.options = f"-p2024 -N -F{os.devnull} -oIdentityFile={thisdir}/ssh/test_ssh_client_rsa_key " \
                           f"-oUserKnownHostsFile={thisdir}/ssh/test_ssh_client_known_hosts"
            # USERNAME is for win32
            self.serverUserName = os.environ.get('USER', os.environ.get('USERNAME'))
        elif self.mode in ('vpn', 'wtf', 'local-noconf'):  # VPN
            self.sshClient = 'manual'
            self.options = ''
        else:
            raise ValueError(f'Unhandled network mode "{mode}" for ssh setup: (must be one of {", ".join(allModes)}).')
