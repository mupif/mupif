import sys
#Import example-wide configuration
sys.path.append('..')
import conf as cfg
import PingServerApplication
applicationClass = PingServerApplication.PingServerApplication
applicationInitialFile = "input.in"#dummy file

nshost = cfg.nshost #NameServer - do not change
nsport = cfg.nsport #NameServer's port - do not change
hkey = cfg.hkey #Password for accessing nameServer and applications

serverUserName=cfg.serverUserName
server = cfg.server#IP of your server
jobManPort=cfg.serverPort #Port for job manager's daemon
serverNathost=cfg.serverNathost
jobManNatport=cfg.serverNatport #Natport - nat port used in ssh tunnel for job manager
jobManName=cfg.jobManName #Name of job manager
jobManSocket=cfg.socketApps #Port used to communicate with application servers

jobManPortsForJobs=cfg.portsForJobs #Range of ports to be assigned on the server to jobs
jobManMaxJobs=cfg.maxJobs #Maximum number of jobs
jobManWorkDir=cfg.jobManWorkDir#Main directory for transmitting files

jobMan2CmdPath = cfg.jobMan2CmdPath # path to JobMan2cmd.py











#daemonHost='147.32.130.137'#IP of server
#hostUserName='mmp'#User name for ssh connection



#jobManPort=44361 #Port for job manager's daemon
#jobManNatport=5555 #Natport - nat port used in ssh tunnel for job manager
#jobManSocket=10001 #Port used to communicate with application servers
#jobManName='Mupif.JobManager@demo' #Name of job manager

#jobManPortsForJobs=( 9091, 9094) #Range of ports to be assigned on the server to jobs
#jobManMaxJobs=4 #Maximum number of jobs
#jobManWorkDir='/home/mmp/PingServerApplication'#Main directory for transmitting files


#jobMan2CmdPath = "../../tools/JobMan2cmd.py" # path to JobMan2cmd.py 
