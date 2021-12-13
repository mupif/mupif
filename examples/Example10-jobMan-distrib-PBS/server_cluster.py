# this script is made for a specific test cluster
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

nshost = '172.22.2.1'
nsport = 10000
ownaddress = '172.22.2.16'

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=nshost, nsport=nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    appClass=application10.Application10,
    server=ownaddress,
    nshost=nshost,
    nsport=nsport,
    ns=ns,
    appName='Mupif.JobManager@Example10_cluster',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
)

mp.pyroutil.runJobManagerServer(
    server=ownaddress,
    port=44382,
    nshost=nshost,
    nsport=nsport,
    jobman=jobMan
)
