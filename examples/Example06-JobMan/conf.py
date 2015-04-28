import sys
sys.path.append('../..')

import PingServerApplication

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

#jobname - do not change 
#jobname = 'PingTest'


nathost='localhost' #nathost - do not change
natport=5555 #natport - nat port used in ssh tunnel destination

nshost = '147.32.130.137' #nameserver - do not change
nsport  = 9090 #name server port - do not change
hkey = 'mmp-secret-key' #password for accessing nameServer and applications

#Job Manager daemon running on a server, same IP as application
jobManDaemon='147.32.130.137'
jobManPort=44361
jobManName='Mupif.JobManager@demo'
jobManPortsForJobs=( 9091, 9092, 9093, 9094)
jobManMaxJobs=4 #Maximum number of jobs
serverUserName='smilauer'

#Job daemon running on a server
jobDaemonPort = 44382
jobDaemonNatPort = 6000



