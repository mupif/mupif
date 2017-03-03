#Common configuration for examples
import sys, os, os.path
import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
Pyro4.config.SERVERTYPE="multiplex"

#Absolute path to mupif directory - used in JobMan2cmd
mupif_dir = os.path.abspath(os.path.join(os.getcwd(), "../../.."))
sys.path.append(mupif_dir)
mupif_dir = os.path.abspath(os.path.join(os.getcwd(), "../.."))
sys.path.append(mupif_dir)

from mupif import logger

#NAME SERVER and SERVER
#IP/name of a name server
nshost = '172.30.0.1'
#Port of name server
nsport = 9090
#Password for accessing nameServer and applications
hkey = 'mupif-secret-key'
#name server's name


#SERVER for a single job or for JobManager
#IP/name of a server's daemon
server = '172.30.0.1'
#Port of server's daemon
serverPort = 44382
#Name of job manager
jobManName='Mupif.JobManager@Example'
#Name of application
appName = 'MuPIFServer'

#Jobs in JobManager
#Range of ports to be assigned on the server to jobs
portsForJobs=( 9095, 9200 )
#Maximum number of jobs
maxJobs=4
#Auxiliary port used to communicate with application daemons on a local computer
socketApps=10000
#Main directory for transmitting files
jobManWorkDir='.'
#Path to JobMan2cmd.py 
jobMan2CmdPath = "../../tools/JobMan2cmd.py"

#SERVER - a second application
server2 = '172.30.0.1'
serverPort2 = 44383

#SERVER - an application running on local computer in VPN
server3 = '172.30.0.6'
serverPort3 = 44385

#Name of the application
appName = 'MuPIFServer'



