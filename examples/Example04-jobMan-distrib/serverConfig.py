# Configuration file for JobMan2cmd
import sys, os.path, os
d=os.path.dirname(os.path.abspath(__file__))
sys.path+=[d+'/..',d+'/../Example02-distrib']
from Config import config
import application2


class serverConfig(config):
    def __init__(self, mode):
        # inherit necessary variables: nshost, nsport, hkey, server, serverNathost
        super(serverConfig, self).__init__(mode)

        self.applicationClass = application2.Application2
        self.applicationInitialFile = os.devnull  # dummy file

