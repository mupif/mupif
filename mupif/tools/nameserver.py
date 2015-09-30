from __future__ import print_function
# This script starts a nameserver for Pyro4 on this machine
# Works with Pyro4 version 4.28 (later 4.39)
# Tested on Ubuntu 14.04 and Win XP (4.39)
# Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz
# TNO 09/2015

import os
import subprocess

def main():
    #Initializating variables
    nshost = 'localhost'
    nsport = 9090
    hkey = 'mmp-secret-key'
    python = 'python'
    os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'
    os.environ['PYRO_PICKLE_PROTOCOL_VERSION']='2'
    os.environ['PYRO_SERIALIZER']='pickle'
    
    #Creation of nameserver
    cmd = '%s -m Pyro4.naming -n %s -p %d -k %s' % (python, nshost, nsport, hkey)
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
    output, error = p.communicate()
    print(output if output else "", error if error else "")


if __name__ == '__main__':
    main()