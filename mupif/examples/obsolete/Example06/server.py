import os,sys
sys.path.append('..')
import conf as cfg
from mupif import *
import Pyro4
import logging
log = logging.getLogger()
util.changeRootLogger('server.log')

import mupif.physics.physicalquantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

#if you wish to run no SSH tunnels, set to True
noSSH=False

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44361 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT

@Pyro4.expose
class PingServerApplication(model.Model):
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
            log.debug('Getting property from PingServerApplication')
            return property.ConstantProperty(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 'kg/m**3', time, 0)
        else:
            raise apierror.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property
        else:
            raise apierror.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib.getValue(tstep.getTime())
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return PQ. PhysicalQuantity(1.0,'s')

    def getApplicationSignature(self):
        return cfg.appName


app2 = PingServerApplication("/dev/null")

if noSSH: #set NATport=port and local IP
    cfg.server = cfg.serverNathost
    cfg.serverNatport = cfg.serverPort

pyroutil.runAppServer(cfg.server, cfg.serverPort, cfg.serverNathost, cfg.serverNatport, 
                      cfg.nshost, cfg.nsport, cfg.appName, cfg.hkey, 
                      app=app2)
