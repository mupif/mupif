#Common configuration for examples
import sys, os, os.path
import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}

#Absolute path to mupif directory - used in JobMan2cmd
mupif_dir = os.path.abspath(os.path.join(os.getcwd(), "../../.."))
sys.path.append(mupif_dir)

import logging

#NAME SERVER
#IP/name of a name server
nshost = '127.0.0.1'
#nshost = '147.32.130.137'
#Port of name server
nsport = 9090
#Password for accessing nameServer and applications
hkey = 'mmp-secret-key'
#name server's name


#SERVER for a single job or for JobManager
#IP/name of a server's daemon
server = '127.0.0.1'
#server = '147.32.130.137'
#Port of server's daemon
serverPort = 44382
#Nat IP/name (necessary for ssh tunnel)
serverNathost = '127.0.0.1'
#Nat port (necessary for ssh tunnel)
serverNatport = 5555
#Name of job manager
jobManName='Mupif.JobManager@Example'
#Name of application class

#Jobs in JobManager
#Range of ports to be assigned on the server to jobs
portsForJobs=( 9095, 9200 )
#NAT client ports used to establish ssh connections
jobNatPorts = list(range(6000, 6050))

#Maximum number of jobs
maxJobs=4
#Auxiliary port used to communicate with application daemons on a local computer
socketApps=10000
#Main directory for transmitting files
jobManWorkDir='.'
#Path to JobMan2cmd.py 
jobMan2CmdPath = "../../tools/JobMan2cmd.py"

#Name of the application
appName = 'MuPIFServer'

#CLIENT
#User name for ssh connection, empty uses current login name
serverUserName = os.environ.get( "USERNAME" )#current user

if(sys.platform.lower().startswith('win')):#Windows ssh client
    sshClient = 'C:\\Program Files\\Putty\\putty.exe'
    options = '-i L:\\.ssh\\mech\id_rsa.ppk'
    sshHost = ''
else:#Unix ssh client
    sshClient = 'ssh'
    options = '-oStrictHostKeyChecking=no'
    sshHost = ''

# this is defined in Travis automatically; do everything locally in that case
if 'TRAVIS' in os.environ:
    nshost='localhost'
    nsport=9090
    server='localhost'
    serverNathost='localhost'
    sshClient='ssh'
    thisdir=os.path.dirname(os.path.abspath(__file__))
    options="-p2024 -N -F/dev/null -v -oIdentityFile=%s/ssh/test_ssh_client_rsa_key -oUserKnownHostsFile=%s/ssh/test_ssh_client_known_hosts"%(thisdir,thisdir)
    sshHosts=''
    serverUserName=os.environ['USER']
    
