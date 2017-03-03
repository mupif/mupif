from __future__ import division
import os,sys
sys.path.append('..')
import conf as cfg
from mupif import *
import mupif
import Pyro4

#if you wish to run no SSH tunnels, set to True
noSSH=False

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44361 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT

@Pyro4.expose
class PingServerApplication(Application.Application):
    """
    Simple application that computes an aritmetical average of a mapped property
    """
    def __init__(self, file):
        super(PingServerApplication,self).__init__(file)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            mupif.log.debug('Getting property from PingServerApplication, exiting')
            return Property.Property(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, None, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
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
        return cfg.appName


app2 = PingServerApplication("/dev/null")

if noSSH: #set NATport=port and local IP
    cfg.server = cfg.serverNathost
    cfg.serverNatport = cfg.serverPort

PyroUtil.runAppServer(cfg.server, cfg.serverPort, cfg.serverNathost, cfg.serverNatport, 
                      cfg.nshost, cfg.nsport, cfg.appName, cfg.hkey, 
                      app=app2)
