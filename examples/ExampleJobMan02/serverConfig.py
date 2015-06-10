import sys
sys.path.append('../..')

import DemoApplication
applicationClass = DemoApplication.DemoApplication

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

nshost = '147.32.130.137' #NameServer - do not change
nsport  = 9090 #NameServer's port - do not change
hkey = 'mmp-secret-key' #Password for accessing nameServer and applications
nathost='127.0.0.1' #NatHost of local computer - do not change

daemonHost='147.32.130.137'#IP of your server
hostUserName='mmp'#User name for ssh connection

jobManPort=44361 #Port for job manager's daemon
jobManNatport=5555 #Natport - nat port used in ssh tunnel for job manager
jobManName='Mupif.JobManager@demo' #Name of job manager

jobManPortsForJobs=(9091, 9094) #Range of ports to be assigned on the server to jobs
jobManMaxJobs=4 #Maximum number of jobs
jobManWorkDir='/tmp/1'#Main directory for transmitting files

