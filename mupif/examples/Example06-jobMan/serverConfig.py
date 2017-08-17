#Configuration file for JobMan2cmd
import os,sys
sys.path.extend(['..','../Example02-distributed'])
from Config import config
import application2

class serverConfig(config):
     def __init__(self,mode):
         #inherit necessary variables: nshost, nsport, hkey, server, serverNathost  
         super(serverConfig, self).__init__(mode)

         self.applicationClass = application2.application2
         self.applicationInitialFile = '/dev/null' #dummy file

