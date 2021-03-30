import os
import sys
import argparse
import logging
rp = os.path.realpath(__file__)
dirname = os.path.dirname(rp)
sys.path.extend([dirname+'/.',dirname+'/..', dirname+'/../..'])
import mupif as mp
log = logging.getLogger()
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg = ExConfig()
import application10

# extend the configuration
cfg.applicationClass = application10.Application10

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    serverConfig=cfg,
    ns=ns,
    appName=cfg.jobManName,
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs,
)

mp.pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    jobman=jobMan
)
