# Thermal server for nonstationary problem
import os
import sys
import argparse

sys.path.extend(['..', '../..', '../06-stacTM-local'])
import mupif as mp
import models

#util.redirectLog('thermal.log')

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=models.ThermalNonstatModel,
    appName='thermal-nonstat-ex08',
).runServer()



