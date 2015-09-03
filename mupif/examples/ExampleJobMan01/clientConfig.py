from builtins import range
import sys
sys.path.append('../..')
sys.path.append('../../tools')

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

nshost = '147.32.130.137' #NameServer - do not change
nsport  = 9090 #NameServer's port - do not change
hkey = 'mmp-secret-key' #Password for accessing nameServer and applications
nathost='127.0.0.1' #NatHost of local computer - do not change

#daemonHost='147.32.130.137'#IP of server
hostUserName='mmp'#User name for ssh connection

if(sys.platform.lower().startswith('win')):#Windows ssh client
    sshClient = 'C:\\Program Files\\Putty\\putty.exe'
    options = '-i L:\\.ssh\\mech\id_rsa.ppk'
    sshHost = ''
else:#Unix ssh client
    sshClient = 'ssh'
    options = '-oStrictHostKeyChecking=no'
    sshHost = ''

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName)
solverJobManRec = (44360, 5555, '147.32.130.137', hostUserName, 'Mupif.JobManager@ExampleJobMan01')


#client ports used to establish ssh connections (nat ports)
jobNatPorts = list(range(6000, 6050))
