# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../..', '../Example06-stacTM-local'])
import mupif as mp
import models

from exconfig import ExConfig
cfg=ExConfig()
cfg.applicationInitialFile='inputT.in' # used?

#util.changeRootLogger('thermal.log')

# locate nameserver
ns = mp.pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=models.ThermalNonstatModel,
    appName='thermal-nonstat-ex08',
    jobManWorkDir=cfg.jobManWorkDir,
    maxJobs=cfg.maxJobs
).runServer()



