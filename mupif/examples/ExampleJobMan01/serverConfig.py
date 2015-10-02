import sys
sys.path.append('..')
from conf import *

import DemoApplication

#print nshost

#nshost = '147.32.130.137' #NameServer hosted on CTU
#nshost = '127.0.0.1' #NameServer on local computer
#nsport  = 9090 #NameServer's port - do not change
#hkey = 'mmp-secret-key' #Password for accessing nameServer and applications
#nathost='127.0.0.1' #NatHost of local computer - do not change

#daemonHost='147.32.130.137'#IP of server
#daemonHost='127.0.0.1'#IP of server
#hostUserName='mmp'#User name for ssh connection

#jobManPort=44360 #Port for job manager's daemon
#jobManNatport=5555 #Natport - nat port used in ssh tunnel for job manager
#jobManSocket=10000 #Port used to communicate with application servers
#jobManName='Mupif.JobManager@ExampleJobMan01' #Name of job manager

#jobManPortsForJobs=( 9095, 9100) #Range of ports to be assigned on the server to jobs
#jobManMaxJobs=4 #Maximum number of jobs
#jobManWorkDir='.'#Main directory for transmitting files

applicationClass = DemoApplication.DemoApplication

#jobMan2CmdPath = "../../tools/JobMan2cmd.py" # path to JobMan2cmd.py 

