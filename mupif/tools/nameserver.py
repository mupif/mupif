# This script starts a nameserver for Pyro4 on this machine
# Works with Pyro4 version 4.28 (later 4.39)
# Tested on Ubuntu 14.04 and Win XP (4.39)
# Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz
# TNO 09/2015

import os, sys
import subprocess
sys.path.append('../examples')
import conf as cfg

def main():
    #Initializating variables
    nshost = cfg.nshost
    nsport = cfg.nsport
    hkey = cfg.hkey
    os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'
    os.environ['PYRO_PICKLE_PROTOCOL_VERSION']='2'
    os.environ['PYRO_SERIALIZER']='pickle'
    os.environ['PYRO_SERVERTYPE']='multiplex'
    
    ##Creation of nameserver
    cmd = 'pyro4-check-config'
    p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, error = p1.communicate()
    print(output.decode('utf-8') if output else "", error if error else "")

    #Able to kill this process by referrring to pyro4-ns
    cmd = 'pyro4-ns -n %s -p %d -k %s' % (nshost, nsport, hkey)
    p2 = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
    output, error = p2.communicate()
    print(output.decode('utf-8') if output else "", error if error else "")

if __name__ == '__main__':
    main()

