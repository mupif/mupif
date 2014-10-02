# This script starts a client for Pyro4 on this machine with Application1
# Works with Pyro4 version 4.28
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 09/2014, vit.smilauer (et) fsv.cvut.cz

#where is a running nameserver
nshost = "127.0.0.1"
nsport = 9090

import sys
sys.path.append('../..')
import os
import logging
logging.basicConfig(filename='client.log',filemode='w',level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen
from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import Property
from mupif import ValueType
import Pyro4
import socket


Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x

class application1(Application.Application):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, file):
        return
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return Property.Property(self.value, PropertyID.PID_Concentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime()
        self.value=1.0*time
    def getCriticalTimeStep(self):
        return 0.1

time  = 0
timestepnumber=0
targetTime = 10.0

#Check connection to a LISTENING port of the nameserver
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    s.connect((nshost, nsport))
    s.shutdown(2)
    print ("Can connect to nameserver's LISTENING port on " + nshost + ":" + str(nsport))
except Exception as e:
    print ("Cannot connect to nameserver's LISTENING port on " + nshost + ":" + str(nsport) + ". Is a Pyro4 nameserver running there? Does a firewall block INPUT or OUTPUT on the port?")
    logging.exception(e)
    exit(0)

#locate nameserver
ns     = Pyro4.locateNS(host=nshost, port=nsport)

#Daemon runs on arbitrary port
daemon = Pyro4.Daemon()

# application1 is local, create its instance
app1 = application1(None)
# application2 is remote, request remote proxy
uri = ns.lookup("Mupif.application2")
print (uri)
app2 = Pyro4.Proxy(uri)

while (abs(time -targetTime) > 1.e-6):
    #determine critical time step
    try:
        dt2 = app2.getCriticalTimeStep()
    except Exception as e:
        print ("Cannot connect to application 2 on uri " + str(uri) + ". Is the server running?" )
        logging.exception(e)
        exit(0)
    dt = min(app1.getCriticalTimeStep(), dt2)
    #update time
    time = time+dt
    if (time > targetTime):
        #make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    print ("Step: ", timestepnumber, time, dt)
    # create a time step
    istep = TimeStep.TimeStep(time, dt, timestepnumber)

    try:
        #solve problem 1
        app1.solveStep(istep)
        #request temperature field from app1
        c = app1.getProperty(PropertyID.PID_Concentration, istep)
        # register temperature field in app2
        app2.setProperty (c)
        # solve second sub-problem 
        app2.solveStep(istep)

        
    except APIError.APIError as e:
        print ("Following API error occurred:",e)
        break

prop = app2.getProperty(PropertyID.PID_CumulativeConcentration, istep)
print  ("Result: ", prop.getValue())
# terminate
app1.terminate();
app2.terminate();
