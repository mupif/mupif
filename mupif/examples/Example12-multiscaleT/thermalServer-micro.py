import os,sys
sys.path.append('..')
import conf as cfg
from mupif import *
import mupif

#import module Example10/demoapp.py
sys.path.append('../Example10')
import demoapp
import logging
logger = logging.getLogger()

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44361 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT

thermalMicro = demoapp.thermal('thermalMicroFile.in','')

PyroUtil.runAppServer(cfg.server, cfg.serverPort, cfg.serverNathost, cfg.serverNatport, 
                      cfg.nshost, cfg.nsport, 'thermalMicro', cfg.hkey, 
                      app=thermalMicro)
