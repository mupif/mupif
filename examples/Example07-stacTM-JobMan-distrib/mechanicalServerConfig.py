import os
import sys
# Import example-wide configuration
sys.path.extend(['..'])
from exconfig import ExConfig
import models


class ServerConfig(ExConfig):
    def __init__(self,*,mode=None):
        super().__init__(mode=mode)
        # Let Daemon run on higher ports
        self.serverPort = self.serverPort+1
        if self.serverNatport is not None:
            self.serverNatport += 1
        self.portsForJobs = (9250, 9300)
        self.jobNatPorts = [None] if self.jobNatPorts[0] is None else list(range(6230, 6300))
        
        self.applicationClass = models.MechanicalModel
        self.applicationInitialFile = 'input.in'  # dummy file
        self.jobManName = 'Mupif.JobManager@MechanicalSolverDemo'  # Name of job manager
        self.jobManWorkDir = os.path.abspath(os.path.join(os.getcwd(), 'mechanicalWorkDir'))
        # self.sshHost = '147.32.130.71'
        self.sshHost = '127.0.0.1'  # ip adress of the server running mechanical server
        
        self.serverPort = 44920
        if self.mode=='ctu-vpn':
            self.serverNathost = '127.0.0.1'
            self.serverNatport = 6050
        else:
            self.serverNatport = None
            self.serverNathost = None
        self.serverUserName = os.environ.get('USER',os.environ.get('USERNAME','[unknown-user]'))
