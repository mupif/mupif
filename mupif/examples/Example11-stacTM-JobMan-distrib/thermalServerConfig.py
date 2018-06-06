import os,sys
#Import example-wide configuration
sys.path.extend(['..', '../Example10-stacTM-local'])
from Config import config
import demoapp

class serverConfig(config):
    def __init__(self,mode):
        #inherit necessary variables: nshost, nsport, hkey, server, serverNathost  
        super(serverConfig, self).__init__(mode)

        self.applicationClass = demoapp.thermal
        self.applicationInitialFile = 'input.in' #dummy file
        self.jobManName='Mupif.JobManager@ThermalSolverDemo'#Name of job manager
        self.jobManWorkDir=os.path.abspath(os.path.join(os.getcwd(), 'thermalWorkDir'))
        self.sshHost = '147.32.130.14' # jaja
        self.serverPort = 44520
        self.serverNatport = 6025
        self.serverNathost = '127.0.0.1'
        self.portsForJobs=( 9718, 9800 )
        self.jobNatPorts = [None] if self.jobNatPorts[0]==None else list(range(7210, 7300))


