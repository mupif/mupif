# This script tests a connection with server on VPN network
# Works with Pyro4 version 4.28
# Tested on Ubuntu 14.04-16.04, Win XP and Win 8.1
# Vit Smilauer 03/2017, vit.smilauer (et) fsv.cvut.cz

import os, sys
sys.path.append('..')
import conf_vpn as cfg
from mupif import *
import mupif

# Test nameserver
ns = PyroUtil.connectNameServer(cfg.nshost, cfg.nsport, cfg.hkey)

# Test remote application2, request remote proxy
app2=PyroUtil.connectApp(ns, cfg.appName)
app2.getApplicationSignature()

# Terminate remote application2
app2.terminate();
