import os,sys
#Import example-wide configuration
sys.path.append('..')
import conf as cfg
import demoapp

nshost = cfg.nshost #NameServer - do not change
nsport = cfg.nsport #NameServer's port - do not change
hkey = cfg.hkey #Password for accessing nameServer and applications
nathost =cfg.serverNathost

hostUserName=cfg.serverUserName#User name for ssh connection
server = cfg.server#IP of server
serverPort = cfg.serverPort
serverNathost = cfg.serverNathost
serverNatport = cfg.serverNatport
jobManSocket=cfg.socketApps #Port used to communicate with application servers
jobManName='Mupif.JobManager@ThermalSolverDemo' #Name of job manager

jobManPortsForJobs=( 9091, 9094) #Range of ports to be assigned on the server to jobs
jobManMaxJobs=4 #Maximum number of jobs
jobManWorkDir=os.path.abspath(os.path.join(os.getcwd(), 'thermalWorkDir'))
'/home/mmp/work/thermalWorkDir'#Main directory for transmitting files

applicationClass = demoapp.thermal
jobMan2CmdPath = cfg.jobMan2CmdPath # path to JobMan2cmd.py
