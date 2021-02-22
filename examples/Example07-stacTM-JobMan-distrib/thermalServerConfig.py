import os
import sys
# Import example-wide configuration
sys.path.append('..')
from Config import config
import models


class serverConfig(config):
    def __init__(self, mode):
        # inherit necessary variables: nshost, nsport, hkey, server, serverNathost
        super(serverConfig, self).__init__(mode)

        self.applicationClass = models.ThermalModel
        self.applicationInitialFile = 'input.in'  # dummy file
        self.jobManName = 'Mupif.JobManager@ThermalSolverDemo'  # Name of job manager
        self.jobManWorkDir = os.path.abspath(os.path.join(os.getcwd(), 'thermalWorkDir'))
        self.sshHost = '127.0.0.1'  # ip adress of the server running thermal server
        self.serverPort = 44820
        if mode == 1:
            self.serverNathost = '127.0.0.1'
            self.serverNatport = 6025
        else:
            self.serverNatport = None
            self.serverNathost = None
        self.portsForJobs = (9718, 9800)
        self.jobNatPorts = [None] if self.jobNatPorts[0] is None else list(range(7210, 7300))
        self.serverUserName = os.environ.get('USER',os.environ.get('USERNAME','[unknown-user]'))
