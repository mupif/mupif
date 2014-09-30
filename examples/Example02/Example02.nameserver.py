#This script starts a nameserver for Pyro4 on this machine
#Works with Pyro4 version 4.28
#Tested on Ubuntu 14.04 and Win XP
#Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz

import os
import subprocess

os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'

cmd = 'pyro4-check-config'
p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
print p1.communicate()[0]

cmd = 'pyro4-ns -n 127.0.0.1'
p2 = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
print p2.communicate()[0]
