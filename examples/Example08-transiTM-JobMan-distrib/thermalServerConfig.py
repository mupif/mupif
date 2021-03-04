# Configuration file for JobMan2cmd
import os
import sys
sys.path.append('..')
from Config import config
import models


class serverConfig(config):
    def __init__(self, mode):
        # inherit necessary variables: nshost, nsport, hkey, server, serverNathost
        super().__init__(mode)

        self.applicationClass = models.ThermalNonstatModel
        self.applicationInitialFile = '..'+os.path.sep+'..'+os.path.sep+'Example06-stacTM-local'+os.path.sep+'inputT10.in'
