# This script starts a nameserver for Pyro4 on this machine
# Works with Pyro4 version 4.28
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz

# The nameserver always starts, even when the port 9090 is blocked by a firewall.
# It is then impossible to connect from a server/client to this port with DROP/REJECT INPUT or OUTPUT status.
# To unblock INPUT, run on Ubuntu
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT

import os
import subprocess

os.environ['PYRO_SERIALIZERS_ACCEPTED'] = 'serpent,json,marshal,pickle'

cmd = 'pyro4-check-config'
p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
print p1.communicate()[0]

cmd = 'pyro4-ns -n 127.0.0.1 -p 9090'
p2 = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
print p2.communicate()[0]
