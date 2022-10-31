# Thermal server for nonstationary problem
import os
import sys
import argparse
sys.path.extend(['..', '../..', '../06-stacTM-local'])
import mupif as mp

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.ThermalNonstatModel,
    appName='thermal-nonstat-ex08',
).runServer()
