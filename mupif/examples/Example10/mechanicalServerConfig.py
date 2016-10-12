import os,sys
#Import example-wide configuration
sys.path.append('..')
import conf as cfg
import demoapp

nshost = cfg.nshost #NameServer - do not change
nsport  = cfg.nsport #NameServer's port - do not change
hkey = cfg.hkey #Password for accessing nameServer and applications
nathost = cfg.serverNathost

hostUserName=cfg.serverUserName#User name for ssh connection
server = cfg.server#IP of server
serverPort = cfg.serverPort+1
serverNathost = cfg.serverNathost
serverNatport = cfg.serverNatport+1
jobManSocket=cfg.socketApps+1 #Port used to communicate with application servers
jobManName='Mupif.JobManager@MechanicalSolverDemo' #Name of job manager


jobManPortsForJobs=( 9095, 9100) #Range of ports to be assigned on the server to jobs
jobManMaxJobs=4 #Maximum number of jobs
jobManWorkDir=os.path.abspath(os.path.join(os.getcwd(), 'mechanicalWorkDir'))
#jobManWorkDir='/home/mmp/work/mechanicalWorkDir'#Main directory for transmitting files
applicationInitialFile = 'input.in'
applicationClass = demoapp.mechanical
jobMan2CmdPath = cfg.jobMan2CmdPath # path to JobMan2cmd.py 
