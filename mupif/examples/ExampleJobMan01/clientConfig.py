from builtins import range
import os,sys
sys.path.append('../..')
sys.path.append('../../tools')

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
hkey = 'mmp-secret-key'

#nshost = '147.32.130.137' #NameServer hosted on CTU
nshost = '127.0.0.1' #NameServer on local computer
nsport  = 9090 #NameServer's port - do not change
hkey = 'mmp-secret-key' #Password for accessing nameServer and applications
nathost='127.0.0.1' #NatHost of local computer - do not change

#hostUserName='mmp'#User name for ssh connection
hostUserName=os.getlogin()#current user

if(sys.platform.lower().startswith('win')):#Windows ssh client
    sshClient = 'C:\\Program Files\\Putty\\putty.exe'
    options = '-i L:\\.ssh\\mech\id_rsa.ppk'
    sshHost = ''
else:#Unix ssh client
    sshClient = 'ssh'
    options = '-oStrictHostKeyChecking=no'
    sshHost = ''

# jobManager records to be used in scenario
# format: (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName)
#solverJobManRec = (44360, 5555, '147.32.130.137', hostUserName, 'Mupif.JobManager@ExampleJobMan01')
solverJobManRec = (44360, 5555, '127.0.0.1', hostUserName, 'Mupif.JobManager@ExampleJobMan01')


#client ports used to establish ssh connections (nat ports)
jobNatPorts = list(range(6000, 6050))
