# This script starts a workflow monitor server on this machine
import os,sys
sys.path.extend(['..', '../..','../examples'])
from mupif import WorkflowMonitor
from mupif import Util
from mupif import PyroUtil
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)

Util.changeRootLogger('monitor.log')

# bp stuff
# cfg.monitorServer='172.30.0.3'


# locate nameserver
ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
monitor = WorkflowMonitor.WorkflowMonitor()
print(monitor.getAllMetadata())
PyroUtil.runAppServer(
    server=cfg.monitorServer,
    port=cfg.monitorPort,
    nathost=None,
    natport=None,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName=cfg.monitorName,
    hkey=cfg.hkey,
    app=monitor
)
