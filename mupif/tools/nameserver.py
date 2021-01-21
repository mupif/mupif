# This script starts a nameserver for Pyro4 on this machine
# Works with Pyro4 version 4.54
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import os
import sys
sys.path.append('../..')
import mupif.pyroutil
import mupif.util
import subprocess
sys.path.append('../examples')
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[mupif.util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)
import logging
log = logging.getLogger()
mupif.util.changeRootLogger('nameserver.log')


def main():
    # Initializating variables
    nshost = cfg.nshost
    nsport = cfg.nsport
    log.info(f"Starting nameserver on {cfg.nshost}:{cfg.nsport}")
    # os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'
    # os.environ['PYRO_PICKLE_PROTOCOL_VERSION'] = '2'
    os.environ['PYRO_SERIALIZER'] = 'serpent'
    os.environ['PYRO_SERVERTYPE'] = 'multiplex'
    mupif.pyroutil.useTestSSL_env(os.environ)
    
    # Creation of nameserver
    cmd = 'pyro5-check-config'
    p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, error = p1.communicate()
    print(output.decode('utf-8') if output else "", error if error else "")

    if 0:
        # Able to kill this process by referrring to pyro5-ns
        cmd = 'pyro5-ns -n %s -p %d' % (cfg.nshost, cfg.nsport)
        p2 = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        output, error = p2.communicate()
        print(output.decode('utf-8') if output else "", error.decode('utf-8') if error else "")
    else:
        import Pyro5.nameserver
        # Pyro5.nameserver.main([sys.excecutable,
        Pyro5.nameserver.start_ns_loop(nshost,nsport)


if __name__ == '__main__':
    main()
