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

solverJobManRec = (cfg.serverPort, cfg.serverNatport, cfg.server, cfg.serverUserName, cfg.jobManName)
solverJobManRecNoSSH = (cfg.serverPort, cfg.serverPort, cfg.serverNathost, cfg.serverUserName, cfg.jobManName)
jobNatPorts = cfg.jobNatPorts


