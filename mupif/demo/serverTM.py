# Thermal server for nonstationary problem
import os
import sys
import argparse
dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.extend([dirname+'/.', dirname+'/..', dirname+'/../..'])
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
