# This file should not be executed by users. Use server.py instead to run a local jobmanager with local nameserver.
#
import os
import sys
import logging
dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.extend([dirname+'/.', dirname+'/..', dirname+'/../..'])
import mupif as mp
log = logging.getLogger()
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg = ExConfig()
import application13

nshost = '172.22.2.1'
nsport = 10000
ownaddress = nshost

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=nshost, nsport=nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    appClass=application13.Application13,
    server=ownaddress,
    nshost=nshost,
    nsport=nsport,
    ns=ns,
    appName='Mupif.JobManager@Example13',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server=ownaddress,
    port=cfg.serverPort,
    nshost=nshost,
    nsport=nsport,
    jobman=jobMan
)
