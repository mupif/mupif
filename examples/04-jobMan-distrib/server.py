import sys
import os
d=os.path.dirname(os.path.abspath(__file__))
sys.path += [d+'/..', d+'/../02-distrib', d+'/../..']
import mupif as mp
mp.util.redirectLog('server.log')
import application2

# locate nameserver
ns = mp.pyroutil.connectNameserver()

# Run job manager on a server
jobMan = mp.SimpleJobManager(
    ns=ns,
    appClass=application2.Application2,
    appName='mupif/example04/jobMan',
).runServer()
