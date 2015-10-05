from builtins import range
import sys
#Import example-wide configuration
sys.path.append('..')
import conf as cfg

nshost = cfg.nshost #NameServer - do not change
nsport = cfg.nsport #NameServer's port - do not change
hkey = cfg.hkey #Password for accessing nameServer and applications

serverUserName=cfg.serverUserName
server = cfg.server#IP of your server

sshClient = cfg.sshClient
options = cfg.options
sshHost = cfg.sshHost

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName)
demoJobManRec = ( cfg.serverPort, cfg.serverNatport, cfg.server, serverUserName, cfg.jobManName )

#client ports used to establish ssh connections (nat ports)
jobNatPorts = cfg.jobNatPorts
