# Mechanical server for nonstationary problem
import os
import sys
import argparse
sys.path.extend(['..', '../..'])
import mupif as mp

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.MechanicalModel,
    appName='mechanical-ex08',
).runServer()
