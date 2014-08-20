import sys
sys.path.append('../..')

from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 


import Pyro4

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44382 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT


class PingServerApplication(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return Property.Property(float(self.value)/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, None, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property.getValue()
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1.0

    def getApplicationSignature(self):
        return "CTU Ping server, version 1.0"


daemon = Pyro4.Daemon(host='mech.fsv.cvut.cz', port=44382, nathost="localhost", natport=5555)
ns     = Pyro4.locateNS(host='147.32.130.137', port=9090)

app2 = PingServerApplication("/dev/null")
#register agent
uri    = daemon.register(app2)
ns.register("Mupif.PingServerApplication", uri)
print uri
daemon.requestLoop()
