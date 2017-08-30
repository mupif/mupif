#Common configuration for running examples in local, ssh or VPN mode
import sys, os, os.path
import Pyro4
import logging
log = logging.getLogger()

class config(object):
    """
    Auxiliary class holding configuration variables for local, ssh, or VPN connection.
    Used mainly in mupif/examples/*
    Numerical value of parameter -m sets up internal variables.
    Typically, -m0 is local configuration, -m1 is ssh configuration, -m2 is VPN configuration, -m3 is VPN emulated as local
    """
    
    def __init__(self,mode):
        self.mode = mode
        if mode not in [0,1,2,3]:
           log.error("Unknown mode -m %d" % mode)
        
        Pyro4.config.SERIALIZER="pickle"
        Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
        Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
        Pyro4.config.SERVERTYPE="multiplex"

        #Absolute path to mupif directory - used in JobMan2cmd
        mupif_dir = os.path.abspath(os.path.join(os.getcwd(), "../../.."))
        sys.path.append(mupif_dir)
        mupif_dir = os.path.abspath(os.path.join(os.getcwd(), "../.."))
        sys.path.append(mupif_dir)
        
        #commmon attributes
        #Password for accessing nameServer and applications
        self.hkey = 'mupif-secret-key'
        #Name of job manager
        self.jobManName='Mupif.JobManager@Example'
        #Name of first application
        self.appName = 'MuPIFServer'

        #Jobs in JobManager
        #Range of ports to be assigned on the server to jobs
        self.portsForJobs=( 9000, 9100 )
        #NAT client ports used to establish ssh connections
        self.jobNatPorts = list(range(6000, 6100))

        #Maximum number of jobs
        self.maxJobs=20
        #Auxiliary port used to communicate with application daemons on a local computer
        self.socketApps=10000
        #Main directory for transmitting files
        self.jobManWorkDir='.'
        #Path to JobMan2cmd.py 
        self.jobMan2CmdPath = "../../tools/JobMan2cmd.py"
        
        if 'TRAVIS' in os.environ:#run everything locally on TRAVIS
            self.mode == 0    
        
        if self.mode == 0:#localhost. Jobmanager uses NAT with ssh tunnels
            #NAME SERVER
            #IP/name of a name server
            self.nshost = '127.0.0.1'
            #self.nshost = '147.32.130.71'
            #Port of name server
            self.nsport = 9090

            #SERVER for a single job or for JobManager
            #IP/name of a server's daemon
            self.server = '127.0.0.1'
            #self.server = '147.32.130.71'
            #Port of server's daemon
            self.serverPort = 44382
            #Nat IP/name (necessary for ssh tunnel)
            self.serverNathost = None
            #Nat port (necessary for ssh tunnel)
            self.serverNatport = None

            #SECOND SERVER for another application on remote computer
            self.server2 = self.server
            self.serverPort2 = 44385
            self.serverNathost2 = self.server
            self.serverNatport2 = 5558
            self.appName2 = 'MuPIFServer2'

            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386
           
        if self.mode == 1:#ssh
            #NAME SERVER
            #IP/name of a name server
            self.nshost = '147.32.130.71'
            #Port of name server
            self.nsport = 9090

            #SERVER for a single job or for JobManager
            #IP/name of a server's daemon
            self.server = '147.32.130.71'
            #Port of server's daemon
            self.serverPort = 44382
            #Nat IP/name (necessary for ssh tunnel)
            self.serverNathost = '127.0.0.1'
            #Nat port (necessary for ssh tunnel)
            self.serverNatport = 5555

            #SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44385
            self.serverNathost2 = self.server2
            self.serverNatport2 = 5558
            self.appName2 = 'MuPIFServer2'
        
        if self.mode == 2:#VPN, no ssh tunnels   
            #NAME SERVER
            #IP/name of a name server
            self.nshost = '172.30.0.1'
            #Port of name server
            self.nsport = 9090
            
            #SERVER for a single job or for JobManager
            #IP/name of a server's daemon
            self.server = '172.30.0.1'
            #Port of server's daemon
            self.serverPort = 44382
            #Nat IP/name
            self.serverNathost = None
            #Nat port
            self.serverNatport = None
            self.jobNatPorts = [None]

            #SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44383
            self.serverNathost2 = None
            self.serverNatport2 = None
            #self.appName2 = 'MuPIFServer2'
           
            #third SERVER - an application running on local computer in VPN
            #this server can be accessed only from script from the same computer
            #otherwise the server address has to be replaced by vpn local adress
            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386

        if self.mode == 3:#VPN emulated as local, no ssh tunnels  
            #NAME SERVER
            #IP/name of a name server
            self.nshost = '127.0.0.1'
            #Port of name server
            self.nsport = 9090
            
            #SERVER for a single job or for JobManager
            #IP/name of a server's daemon
            self.server = '127.0.0.1'
            #Port of server's daemon
            self.serverPort = 44382
            #Nat IP/name
            self.serverNathost = None
            #Nat port
            self.serverNatport = None
            self.jobNatPorts = [None]


            #SECOND SERVER for another application (usually runs locally)
            self.server2 = '127.0.0.1'
            self.serverPort2 = 44383
            #self.serverNathost2 = self.server2
            #self.serverNatport2 = 5558
            #self.appName2 = 'MuPIFServer2'
           
            #third SERVER - an application running on local computer in VPN
            #this server can be accessed only from script from the same computer
            #otherwise the server address has to be replaced by vpn local adress
            self.server3 = '127.0.0.1'
            self.serverPort3 = 44386


        self.sshHost = ''
        #SSH CLIENT
        #User name for ssh connection, empty uses current login name
        #serverUserName = os.environ.get( "USERNAME" )#current user-not working
        if 'TRAVIS' in os.environ:
                thisdir=os.path.dirname(os.path.abspath(__file__))
                self.sshClient = 'ssh'
                self.options="-p2024 -N -F/dev/null -oIdentityFile=%s/ssh/test_ssh_client_rsa_key -oUserKnownHostsFile=%s/ssh/test_ssh_client_known_hosts"%(thisdir,thisdir)
                self.serverUserName=os.environ['USER']    
        elif (mode==0 or mode==1):
            self.serverUserName = os.getenv('USER')
            if(sys.platform.lower().startswith('win')):#Windows ssh client
                self.sshClient = 'C:\\Program Files\\Putty\\putty.exe'
                self.options = '-i L:\\.ssh\\mech\id_rsa.ppk'
            else:#Unix ssh client
                self.sshClient = 'ssh'
                self.options = '-oStrictHostKeyChecking=no'
        elif (mode==2 or mode==3):#VPN
            self.sshClient='manual'
            self.options = ''
           
            
