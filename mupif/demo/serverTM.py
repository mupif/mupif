# Thermal server for nonstationary problem
import os
import sys
import argparse
sys.path.extend([os.path.dirname(os.path.abspath(__file__))+'/..', os.path.dirname(os.path.abspath(__file__))+'/../..'])
import mupif as mp

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.ThermalModel,
    appName='CVUT.Thermal_demo',
    maxJobs=100
).runServer()
