import os
import sys
import logging
rp = os.path.realpath(__file__)
dirname = os.path.dirname(rp)
sys.path.extend([dirname+'/.', dirname+'/..', dirname+'/../..'])
import mupif as mp
log = logging.getLogger()
mp.util.changeRootLogger('server.log')
from exconfig import ExConfig
cfg = ExConfig()
import application10

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost='172.22.2.1', nsport=10000)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    appClass=application10.Application10,
    server='172.22.2.16',
    nshost='172.22.2.1',
    nsport=10000,
    ns=ns,
    appName='Mupif.JobManager@Example10',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server='172.22.2.16',
    port=44382,
    nshost='172.22.2.1',
    nsport=10000,
    jobman=jobMan
)
