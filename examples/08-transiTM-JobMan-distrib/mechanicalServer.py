# Mechanical server for nonstationary problem
import os
import sys
import argparse
sys.path.extend(['..', '../..'])
import mupif as mp
import models

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=models.MechanicalModel,
    appName='mechanical-ex08',
).runServer()
