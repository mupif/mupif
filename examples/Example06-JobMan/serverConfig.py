import sys
sys.path.append('../..')

import PingServerApplication

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

nshost = '147.32.130.137' #NameServer - do not change
nsport  = 9090 #NameServer's port - do not change
hkey = 'mmp-secret-key' #Password for accessing nameServer and applications
nathost='127.0.0.1' #NatHost of local computer - do not change

deamonHost='147.32.130.137'#IP of server
hostUserName='mmp'#User name for ssh connection

jobManPort=44361 #Port for job manager's daemon
jobManNatport=5555 #Natport - nat port used in ssh tunnel for job manager
jobManName='Mupif.JobManager@demo' #Name of job manager

jobManPortsForJobs=( 9091, 9092, 9093, 9094) #Ports to be assigned on the server to a job
jobManMaxJobs=4 #Maximum number of jobs

applicationClass = PingServerApplication.PingServerApplication
