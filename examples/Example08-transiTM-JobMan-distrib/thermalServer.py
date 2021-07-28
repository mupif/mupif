# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../..', '../Example06-stacTM-local'])
#from mupif import *
import mupif as mp
import models

from exconfig import ExConfig
cfg=ExConfig()
cfg.applicationInitialFile='inputT.in' # used?

#util.changeRootLogger('thermal.log')

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon for jobMamager on this machine
#daemon = mp.pyroutil.runDaemon(
#    host=cfg.server, port=list(range(cfg.serverPort,cfg.serverPort+100)), nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    appClass=models.ThermalNonstatModel,
    server=cfg.server,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    ns=ns,
    appName='thermal-nonstat-ex08',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    jobman=jobMan
)



