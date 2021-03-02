# This script starts a nameserver for Pyro4 on this machine
# Works with Pyro4 version 4.54
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 07/2017, vit.smilauer (et) fsv.cvut.cz

import os
import sys
sys.path.append('..')
import mupif.pyroutil
import mupif.util
import subprocess
sys.path.append('../examples')
import argparse
import threading
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[mupif.util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)
import logging
log = logging.getLogger()

threading.current_thread().setName('Pyro5-NameServer')
# mupif.util.changeRootLogger('nameserver.log')

def main():
    # Initializating variables
    nshost = cfg.nshost
    nsport = cfg.nsport
    log.warning(f"Starting nameserver on {cfg.nshost}:{cfg.nsport}")
    # os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'
    # os.environ['PYRO_PICKLE_PROTOCOL_VERSION'] = '2'
    
    # equivalent, does not need subprocess and shell etc
    import Pyro5.configure
    Pyro5.configure.SERIALIZER='serpent'
    Pyro5.configure.PYRO_SERVERTYPE='multiplex'
    Pyro5.configure.PYRO_SSL=0

    log.warning(Pyro5.configure.global_config.dump())
    import Pyro5.nameserver
    Pyro5.nameserver.start_ns_loop(nshost,nsport)


if __name__ == '__main__':
    main()
