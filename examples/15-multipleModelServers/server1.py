import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

# locate nameserver
ns = mp.pyroutil.connectNameserver()

jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=mp.demo.ThermalModel,
    appName='model',
).runServer()
