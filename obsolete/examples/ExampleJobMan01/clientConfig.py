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
serverPort = cfg.serverPort
serverNathost = cfg.serverNathost
serverNatport = cfg.serverNatport
serverUserName = cfg.serverUserName
jobManName = cfg.jobManName

sshClient = cfg.sshClient
options = cfg.options
sshHost = cfg.sshHost

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName)
# solverJobManRec = (44360, 5555, '147.32.130.137', hostUserName, 'Mupif.JobManager@ExampleJobMan01')
solverJobManRec = (cfg.serverPort, cfg.serverNatport, cfg.server, cfg.serverUserName, cfg.jobManName)

#client ports used to establish ssh connections (nat ports)
jobNatPorts = cfg.jobNatPorts
