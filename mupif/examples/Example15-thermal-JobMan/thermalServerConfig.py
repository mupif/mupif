import os,sys
#Import example-wide configuration
#path to demoapp.py
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

