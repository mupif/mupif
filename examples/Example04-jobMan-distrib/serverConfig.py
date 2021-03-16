# Configuration file for JobMan2cmd
import sys, os.path, os
d=os.path.dirname(os.path.abspath(__file__))
sys.path+=[d+'/..',d+'/../Example02-distrib']
from exconfig import ExConfig
cfg=ExConfig()
import application2


class ServerConfig(ExConfig):
    def __init__(self,*,mode):
        super().__init__(mode=mode)
        self.applicationClass = application2.Application2
        self.applicationInitialFile = os.devnull  # dummy file

