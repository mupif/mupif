import os
import sys
import logging
dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.extend([dirname+'/.', dirname+'/..', dirname+'/../..'])
import mupif as mp
log = logging.getLogger()
mp.util.redirectLog('server.log')
import application13

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
mp.SimpleJobManager(
    ns=ns,
    appClass=application13.Application13,
    appName='CVUT.demo01',
    maxJobs=100,  # can run simultaneously
).runServer()
