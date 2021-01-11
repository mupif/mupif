import sys
sys.path.extend(['..','../../..','../Example10'])
import demoapp
from mupif import *
import time
import logging
log = logging.getLogger()

import mupif.physics.physicalquantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

appRec = None
## 1-Local setup - nameserver, mechanical server, thermal server, steering script run on a local machine ##
#import conf as cfg
#locate nameserver
#ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
#Locate thermal server
#thermal = pyroutil.connectApp(ns, 'thermalServer1')

## 2-Distributed setup using VPN and peer-to-peer connection. Nameserver remote, thermal server remote.
## Mechanical server local, steering script local
#import conf_vpn as cfg
#ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
#Locate thermal server
#thermal = pyroutil.connectApp(ns, 'thermalServer1')

## 3-Distributed setup using VPN and jobManager connection. Nameserver remote, thermal server remote 
## via job Manager.
## Mechanical server local, steering script local
import conf_vpn as cfg
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
thermalJobMan = pyroutil.connectJobManager(ns, cfg.jobManName)
#solverJobManRecNoSSH = (cfg.serverPort, cfg.serverPort, cfg.server, '', 'jobMan1')

try:
    thermal = pyroutil.allocateApplicationWithJobManager( ns, thermalJobMan, cfg.serverNatport, pyroutil.SSHContext(userName='', sshClient=cfg.sshClient, options='', sshHost = '' ))
    #appRec = pyroutil.allocateApplicationWithJobManager( ns, solverJobManRecNoSSH, -1, sshClient='manual' )
    log.info("Allocated application %s" % thermal.getApplicationSignature())
except Exception as e:
    log.exception(e)

#Common part
log.info(thermal.getApplicationSignature())
#Locate mechanical server
mechanical = pyroutil.connectApp(ns, 'mechanicalServer1')
log.info(mechanical.getApplicationSignature())
#Solve thermal part
tstep = timestep.TimeStep(0,1,1,timeUnits)
thermal.solveStep(tstep)
temperature = thermal.getField(FieldID.FID_Temperature, tstep.getTime())
temperature.field2VTKData().tofile('thermalVTK')
temperature.field2Image2D(title='Thermal', fileName='thermal.png')
#thermal.terminate()

#Solve mechanical part
log.info(mechanical.getApplicationSignature())
mechanical.setField(temperature)
mechanical.solveStep(tstep)
displacement = mechanical.getField(FieldID.FID_Displacement, tstep.getTime())
displacement.field2VTKData().tofile('mechanicalVTK')
displacement.field2Image2D(fieldComponent=1, title='Mechanical', fileName='mechanical.png')
#mechanical.terminate()

if appRec: appRec.terminateAll()

time.sleep(10)
