#Configuration file for JobMan2cmd
import os,sys
sys.path.extend(['..', '../Example06-stacTM-local'])
from Config import config
import demoapp

class serverConfig(config):
    def __init__(self,mode):
        #inherit necessary variables: nshost, nsport, hkey, server, serverNathost  
        super(serverConfig, self).__init__(mode)

        self.applicationClass = demoapp.thermal_nonstat
        self.applicationInitialFile = '..'+os.path.sep+'..'+os.path.sep+'Example06-stacTM-local'+os.path.sep+'inputT10.in'
