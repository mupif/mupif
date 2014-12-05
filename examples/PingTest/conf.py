# List of job applications - server details
# Do not use a dictionary - items are in arbitrary order
# The format is (name, serverName, username, localNATPort, serverPort,sshClient, options, sshHost)

#      ('micress','acsrvappmic1.access.rwth-aachen.de', 'mmp', 5556, 44382,'C:\\Program Files\\Putty\putty.exe','-i C:\\tmp\\FIT-public-SSH2.ppk')]
import sys



if(sys.platform.lower().startswith('win')):
    sshClient = 'C:\\Program Files\\Putty\\putty.exe'
    options = '-i L:\\.ssh\\mech\id_rsa.ppk'
    sshPortSpec = ' -P '
else:
    sshClient = 'ssh'
    options = '-oStrictHostKeyChecking=no -i /home/smilauer/.ssh/mech/id_rsa'
    sshPortSpec = ' -p '


apps=[('ctu-server','147.32.130.137', 'mmp', 5554, 44382, sshClient,options,''),
      ('micress','acsrvappmic1.access.rwth-aachen.de', 'mmp', 5556, 44382, sshClient, options, ''),
      ('mmpraytracer','mmpserver.erve.vtt.fi', 'tracer-user', 5557, 44382, sshClient, options, ''),
      ('celsian','192.168.16.6', 'ctu', 5555, 44381, sshClient, options+sshPortSpec+'223', 'remote.celsian.nl')
      ]
      
      
      #('ctu-server','ksm.fsv.cvut.cz', 'mmp', 5554, 44382, 'C:\\Program Files (x86)\\Putty\\putty.exe','-i C:\\Users\mmp\mupif-code\\id_rsa-putty-private.ppk'),
      #('celsian','jaja.fsv.cvut.cz', 'bp', 5555, 44381,'ssh',''),
      #('micress','acsrvappmic1.access.rwth-aachen.de', 'mmp', 5556, 44382,'C:\\Program Files\\Putty\putty.exe','-i C:\\tmp\\id_rsa-putty-private.ppk')]
      #('micress','acsrvappmic1.access.rwth-aachen.de', 'mmp', 5556, 44382,'ssh',''),
      #('mmpraytracer','mmpserver.erve.vtt.fi', 'tracer-user', 5557, 44382, 'ssh',''),
      #('local','localhost', 'mmp', 44382, 44382, 'manual','-oStrictHostKeyChecking=no')
      #('mmpraytracer','mmpserver.erve.vtt.fi', 'tracer-user', 5557, 44382, 'ssh','')
      

#jobname - do not change 
jobname = 'PingTest'
#nathost - do not change
nathost='localhost'
#nameserver - do not change
nshost = '147.32.130.137'
#name server port - do not change
nsport  = 9090
#password for accessing nameServer and applications
hkey = 'mmp-secret-key'

#do-not-change below this line, indexes in apps list
appIndx_Name = 0
appIndx_ServerName = 1
appIndx_UserName = 2
appIndx_NATPort = 3
appIndx_RemotePort = 4
appIndx_SshClient = 5
appIndx_Options = 6
appIndx_SshHost = 7

import logging
#put logging before Pyro4 module
logging.basicConfig(filename='mupif.pyro.log',filemode='w',datefmt="%Y-%m-%d %H:%M:%S",level=logging.DEBUG)
logging.getLogger('Pyro4').setLevel(logging.DEBUG)
#logging.getLogger('Pyro4.core').setLevel(logging.DEBUG)#To handle LOGWIRE
logger = logging.getLogger('test.py')
logger.setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler()) #display logging also on screen

import Pyro4
Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
#Pyro4.config.LOGWIRE=True

