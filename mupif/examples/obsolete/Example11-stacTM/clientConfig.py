from builtins import range
import os,sys
sys.path.append('..')
import conf as cfg

nshost = cfg.nshost #NameServer - do not change
nsport  = cfg.nsport #NameServer's port - do not change
hkey = cfg.hkey #Password for accessing nameServer and applications
nathost=cfg.serverNathost

hostUserName=cfg.serverUserName#User name for ssh connection

sshClient = cfg.sshClient
options = cfg.options
sshHost = cfg.sshHost

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName)
thermalSolverJobManRec = (cfg.serverPort, cfg.serverNatport, cfg.server, hostUserName, 'Mupif.JobManager@ThermalSolverDemo')

#cfg.server = '147.32.130.137'

mechanicalSolverJobManRec = (cfg.serverPort+1, cfg.serverNatport+1, cfg.server, hostUserName, 'Mupif.JobManager@MechanicalSolverDemo')


#client ports used to establish ssh connections (nat ports)
jobNatPorts = cfg.jobNatPorts

