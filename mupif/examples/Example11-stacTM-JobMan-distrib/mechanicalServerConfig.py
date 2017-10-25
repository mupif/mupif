import os,sys
#Import example-wide configuration
sys.path.extend(['..', '../Example10-stacTM-local'])
from Config import config
import demoapp

class serverConfig(config):
    def __init__(self,mode):
        #inherit necessary variables: nshost, nsport, hkey, server, serverNathost  
        super(serverConfig, self).__init__(mode)
        #Let Daemon run on higher ports
        self.serverPort = self.serverPort+1
        if self.serverNatport != None:
            self.serverNatport+=1
        self.socketApps = self.socketApps+1
        self.portsForJobs=( 9200, 9300 )
        self.jobNatPorts = [None] if self.jobNatPorts[0]==None else list(range(6200, 6300)) 
        
        self.applicationClass = demoapp.mechanical
        self.applicationInitialFile = 'input.in' #dummy file
        self.jobManName='Mupif.JobManager@MechanicalSolverDemo'#Name of job manager
        self.jobManWorkDir=os.path.abspath(os.path.join(os.getcwd(), 'mechanicalWorkDir'))
