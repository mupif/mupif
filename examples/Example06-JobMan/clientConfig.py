import sys
sys.path.append('../..')

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

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName)
demoJobManRec = (44361, 5555, 'ksm.fsv.cvut.cz', 'mmp', 'Mupif.JobManager@demo')

#client ports used to establish ssh connections (nat ports)
jobNatPorts = range(6000, 6050) 
