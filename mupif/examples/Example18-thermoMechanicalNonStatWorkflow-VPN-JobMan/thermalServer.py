import os,sys
sys.path.extend(['..','../../..','../Example10'])
from mupif import *
import demoapp
Util.changeRootLogger('thermal.log')
import Pyro4
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg=config(mode)

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
#Run a daemon for jobManager on this machine
daemon = Pyro4.Daemon(host=cfg.server, port=cfg.serverPort)

#Run job manager on a server
jobMan = SimpleJobManager.SimpleJobManager2(daemon, ns, None, cfg.jobManName, cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(), 'thermalServerConfig', cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

PyroUtil.runJobManagerServer(server=cfg.server, port=cfg.serverPort, nathost='', natport='', nshost=cfg.nshost, nsport=cfg.nsport, appName=cfg.jobManName, hkey=cfg.hkey, jobman=jobMan, daemon=daemon)



