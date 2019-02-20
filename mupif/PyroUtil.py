#
#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2014 Borek Patzak
#
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301  USA
from builtins import str
import os
import re
import Pyro4
import socket
import getpass
import subprocess
import time
from . import RemoteAppRecord
from . import Model
from . import JobManager
from . import Util
from . import APIError
import logging
log = logging.getLogger()

Pyro4.config.SERIALIZER="pickle"
# some versions of Pyro don't have this attribute... (strange, is documented)
if hasattr(Pyro4.config,'PICKLE_PROTOCOL_VERSION'):
    Pyro4.config.PICKLE_PROTOCOL_VERSION=2 # use lower version for interoperability between python 2 and 3
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}
#Pyro4.config.THREADPOOL_SIZE=100
Pyro4.config.SERVERTYPE="multiplex"

#pyro4 nameserver metadata
NS_METADATA_jobmanager="type:jobmanager"
NS_METADATA_appserver="type:appserver"
NS_METADATA_host='host'
NS_METADATA_port='port'
NS_METADATA_nathost='nathost'
NS_METADATA_natport='natport'


class SSHContext(object):
    """
    Helper class to store ssh tunnel connection details. It is parameter to different methods (connectJobManager, allocateApplicationWithJobManager, etc.).
    When provided, the corresponding ssh tunnel connection is established and associated to proxy using decorator class to make sure it can be terminated properly.
    """
    def __init__(self, userName='', sshClient='manual', options='', sshHost=''):
        self.userName = userName
        self.sshClient=sshClient
        self.options=options
        self.sshHost=sshHost
        

class sshTunnel(object):
    """
    Helper class to represent established ssh tunnel. It defines terminate and __del__ method
    to ensure correct tunnel termination.
    """
    def __init__(self, remoteHost, userName, localPort, remotePort, sshClient='ssh', options='', sshHost='', Reverse=False):
        """ 
        Constructor. Automatic creation of ssh tunnel, using putty.exe for Windows and ssh for Linux.

        :param str remoteHost: IP of remote host
        :param str userName: User name, if empty, current user name is used
        :param int localPort: Local port
        :param int remotePort: Remote port
        :param str sshClient: Path to executable ssh client (on Windows use double backslashes 'C:\\Program Files\\Putty\putty.exe')
        :param str options: Arguments to ssh clinent, e.g. the location of private ssh keys
        :param str sshHost: Computer used for tunelling, optional. If empty, equals to remoteHost
        :param bool Reverse: True if reverse tunnel to be created (default is False)
        
        :raises Exception: if creation of a tunnel failed
        """

        if sshHost =='':
            sshHost = remoteHost
        if userName =='':
            userName = os.getenv('USER')
                
        direction = 'L'
        if Reverse == True:
            direction = 'R'

        #use direct system command. Paramiko or sshtunnel do not work.
        #put ssh public key on a server - interaction with a keyboard
        #for password will not work here (password goes through TTY, not stdin)
        cmd=''
        if sshClient=='ssh':
            cmd = 'ssh -%s %s:%s:%s %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            log.debug("Creating ssh tunnel via command: " + cmd)
        elif sshClient=='autossh':
            cmd = 'autossh -%s %s:%s:%s %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            log.debug("Creating autossh tunnel via command: " + cmd)
        elif 'putty' in sshClient.lower():
            #need to create a public key *.ppk using puttygen.
            #It can be created by importing Linux private key.
            #The path to that key is given as -i option
            cmd = '%s -%s %s:%s:%s %s@%s -N %s' % (sshClient, direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            log.debug("Creating ssh tunnel via command: " + cmd)
        elif sshClient=='manual':
            #You need ssh server running, e.g. UNIX-sshd or WIN-freesshd
            print(direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            cmd1 = 'ssh -%s %s:%s:%s %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            cmd2 = 'putty.exe -%s %s:%s:%s %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            log.info("If ssh tunnel does not exist and you need it, do it manually using a command e.g. " + cmd1 + " , or " + cmd2)
            self.tunnel = 'manual'
        else:
            log.error("Unknown ssh client, exiting")
            exit(0)
        try:
            if (cmd):
                self.tunnel = subprocess.Popen(cmd.split())
        except Exception:
            log.exception("Creation of a tunnel failed. Can not execute the command: %s " % cmd)
            raise

        time.sleep(1.0)

    def terminate(self):
        """
        Terminate the connection.
        """
        if self.tunnel:
            if not self.tunnel == "manual":
                self.tunnel.terminate()
                self.tunnel = None

    def __del__(self):
        self.terminate()
        
                
        


#First, check that we can connect to a listening port of a name server
#Second, connect there
def connectNameServer(nshost, nsport, hkey, timeOut=3.0):
    """
    Connects to a NameServer.

    :param str nshost: IP address of nameServer
    :param int nsport: Nameserver port.
    :param str hkey: A password string
    :param float timeOut: Waiting time for response in seconds
    :return: NameServer
    :rtype: Pyro4.naming.Nameserver
    :raises Exception: When can not connect to a LISTENING port of nameserver
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeOut)
        try: #Treat socket connection problems separately
            s.connect((nshost, nsport))
        except socket.error as msg:
            raise Exception('Socket connection error to nameServer')
            #log.exception(msg)
        s.close()
        log.debug("Can connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport))
    except Exception:
        msg = "Can not connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport) + ". Does a firewall block INPUT or OUTPUT on the port? Exiting."
        log.exception(msg)
        raise

    #locate nameserver
    try:
        ns = Pyro4.locateNS(host=nshost, port=int(nsport), hmac_key=hkey)
        msg = "Connected to NameServer on %s:%s. Pyro4 version on your localhost is %s" %(nshost, nsport, Pyro4.constants.VERSION)
        log.debug(msg)
    except Exception:
        msg = "Can not connect to NameServer on %s:%s. Is the NameServer running? Runs the NameServer on the same Pyro version as this version %s? Do you have the correct hmac_key (password is now %s)? Exiting." %(nshost, nsport, Pyro4.constants.VERSION, hkey)
        log.exception(msg)
        raise

    return ns



def getNSmetadata(ns, name):
    """
    Returns name server metadata for given entry identified by name
    :return entry metadata 
    :rtype: list of strings
    """
    (uri, mdata) = ns.lookup(name, return_metadata=True)
    return mdata

def getNSConnectionInfo(ns, name):
    """
    Returns component connection information stored in name server 
    :return (host, port, nathost, natport) tuple
    :rtype: tuple
    """
    mdata = getNSmetadata(ns, name)
    host=None
    port=None
    nathost=None
    natport=None
    
    for i in mdata:
        match = re.search('\A'+NS_METADATA_host+':([\w\.]+)', i)
        if (match):
            host=match.group(1)
        match = re.search('\A'+NS_METADATA_port+':(\w+)', i)
        if match:
            port=int(match.group(1))
        match = re.search('\A'+NS_METADATA_nathost+':([\w\.]+)', i)
        if match:
            nathost=match.group(1)
        match = re.search('\A'+NS_METADATA_natport+':(\w+)', i)
        if match:
            natport=match.group(1)
        
    return (host, port, nathost, natport)
            

def _connectApp(ns, name, hkey):
    """
    Connects to a remote application.

    :param Pyro4.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :param str hkey: A password string
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application
    """
    try:
        uri = ns.lookup(name)
        log.debug("Application %s, found URI %s on %s from a nameServer %s" % (name, uri, getNSConnectionInfo(ns,name), ns) )
        app2 = Pyro4.Proxy(uri)
        app2._pyroHmacKey = hkey.encode(encoding='UTF-8')
    except Exception as e:
        log.error("Cannot find registered server %s on %s" % (name, ns) )
        raise

    try:
        log.info("Connecting to application %s with %s"%(name, app2))
        sig = app2.getApplicationSignature()
        log.debug("Connected to " + sig + " with the application " + name)
    except Pyro4.errors.CommunicationError as e:
        log.error("Communication error, perhaps a wrong key hkey=%s?" % hkey)
        raise
    except Exception as e:
        log.exception("Cannot connect to application " + name + ". Is the server running?")
        raise

    return app2

def connectApp(ns, name, hkey, sshContext=None):
    """
    Connects to a remote application, creates the ssh tunnel if necessary

    :param Pyro4.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :param str hkey: A password string
    :return: Application Decorator (docorating pyro proxy with ssh tunnel instance)
    :rtype: Instance of an application decorator
    :raises Exception: When cannot find registered server or Cannot connect to application
    """
    tunnel = None
    if sshContext:
        try:
            (hostname, port, natHost, natport) = getNSConnectionInfo(ns, name)
            tunnel = sshTunnel(remoteHost=hostname, userName=sshContext.userName, localPort=natport, remotePort=port,
                               sshClient=sshContext.sshClient, options=sshContext.options, sshHost=sshContext.sshHost)
        except Exception:
            log.exception('Creating ssh tunnel failed for remoteHost %s userName %s localPort %s remotePort %s sshClient %s options %s sshHost %s' %
                          (jobManHostname, sshContext.userName, jobManNatport, jobManPort, sshContext.sshClient, sshContext.options, sshContext.sshHost))
            raise

    app = _connectApp(ns, name, hkey)
    return Model.RemoteModel (app, appTunnel=tunnel)

def getNSAppName(jobname, appname):
    """
    Get application name.

    :param str jobname: Arbitrary string concatenated in the outut
    :param str appname: Arbitrary string concatenated in the outut
    :return: String of concatenated arguments
    :rtype: str
    """
    return 'Mupif'+'.'+jobname+'.'+appname

def runDaemon(host, port, hkey, nathost=None, natport=None):
    """
    Runs a daemon without registering to a name server
    :param str(int) host: Host name where daemon runs. This is typically a localhost
    :param int or tuple port: Port number where daemon will listen (internal port number) or tuple of possible ports
    :param str hkey: A password string
    :param str(int) nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port, optional (external port)

    :return Instance of the running daemon, None if a problem
    :rtype Pyro4.Daemon
    """
    
    if isinstance (port, (tuple, list)):
        ports = port
    else:
        ports = (port,)

    for iport in ports:
        try:
            daemon = Pyro4.Daemon(host=host, port=int(iport), nathost=nathost, natport=Util.NoneOrInt(natport))
            daemon._pyroHmacKey = hkey.encode(encoding='UTF-8')
            log.info('Pyro4 daemon runs on %s:%s using nathost %s:%s' % (host, iport, nathost, natport))
            return daemon
        except socket.error as e:
            log.debug('Socket port %s:%s seems to be already in use' % (host,iport))
            daemon = None
            #raise e
        except Exception:
            log.exception('Can not run Pyro4 daemon on %s:%s using nathost %s:%s' % (host, iport, nathost, natport))
            daemon = None
            #raise
    
    raise APIError ('Can not run Pyro4 daemon on configured ports')


    return daemon

def runServer(server, port, nathost, natport, nshost, nsport, appName, hkey, app, daemon=None, metadata=None):
    """
    Runs a simple application server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str appName: Name of registered application
    :param instance app: Application instance
    :param str hkey: A password string
    :param daemon: Reference to already running daemon, if available. Optional parameter.
    :param metadata: set of strings that will be the metadata tags associated with the object registration. See PyroUtil.py for valid tags. The metadata string "connection:server:port:nathost:natport" will be automatically generated.

    :raises Exception: if can not run Pyro4 daemon
    """
    externalDaemon = False
    if not daemon:
        try:
            daemon = Pyro4.Daemon(host=server, port=int(port), nathost=nathost, natport=Util.NoneOrInt(natport))
            daemon._pyroHmacKey = hkey.encode(encoding='UTF-8')
            log.info('Pyro4 daemon runs on %s:%s using nathost %s:%s' % (server, port, nathost, natport))
        except Exception:
            log.exception('Can not run Pyro4 daemon on %s:%s using nathost %s:%s' % (server, port, nathost, natport))
            raise
            exit(1)
    else:
        externalDaemon = True

    ns = connectNameServer(nshost, nsport, hkey)
    #register agent; register exposed class 
    #ExposedApp = Pyro4.expose(app)172.30.0.1
    #Check if application name already exists on a nameServer
    try:
        (uri, mdata) = ns.lookup(appName, return_metadata=True)
    except Pyro4.errors.NamingError:
        pass
    else:
        log.warning('Application name \'%s\' is already registered on name server, overwriting.' % appName)
    
    uri = daemon.register(app)
    try:
        app.registerPyro(daemon, ns, uri, appName, externalDaemon=externalDaemon)
    except AttributeError as e:
        # catch attribute error (thrown when method not defined)
        log.warning('Can not register daemon for application %s' % appName)
    except:
        log.exception('Can not register daemon on %s:%s using nathost %s:%s on nameServer' % (server, port, nathost, natport))
        raise
        exit(1)
    # generate connection metadata entry
    metadata.add('%s:%s'%(NS_METADATA_host, server))
    metadata.add('%s:%s'%(NS_METADATA_port, port))
    metadata.add('%s:%s'%(NS_METADATA_nathost, nathost))
    metadata.add('%s:%s'%(NS_METADATA_natport, natport))
    ns.register(appName, uri, metadata=metadata)

    log.debug('NameServer %s has registered uri %s' % (appName, uri) )
    log.debug('Running runAppServer: server:%s, port:%s, nathost:%s, natport:%s, nameServer:%s, nameServerPort:%s, applicationName:%s, daemon URI %s' % (server, port, nathost, natport, nshost, nsport, appName, uri) )
    daemon.requestLoop()


def runAppServer(server, port, nathost, natport, nshost, nsport, appName, hkey, app, daemon=None):
    """
    Runs a simple application server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str appName: Name of registered application
    :param instance app: Application instance
    :param str hkey: A password string
    :param daemon: Reference to already running daemon, if available. Optional parameter.

    :raises Exception: if can not run Pyro4 daemon
    """
    runServer(server=server, port=port, nathost=nathost, natport=natport, nshost=nshost, nsport=nsport, appName=appName, hkey=hkey, app=app, daemon=daemon, metadata={NS_METADATA_appserver})


def runJobManagerServer(server, port, nathost, natport, nshost, nsport, appName, hkey, jobman, daemon=None):
    """
    Registers and runs given jobManager server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str appName: Name of job manager to be registered at nameserver
    :param str hkey: A password string
    :param instance app: Application instance
    :param daemon: Reference to already running daemon, if available. Optional parameter.
    """
    runServer(server=server, port=port, nathost=nathost, natport=natport, nshost=nshost, nsport=nsport, appName=appName, hkey=hkey, app=jobman, daemon=daemon, metadata={NS_METADATA_jobmanager})

#def connectApplicationsViaClient(fromSolverAppRec, toApplication, sshClient='ssh', options=''):
def connectApplicationsViaClient(fromContext, fromApplication, toApplication):
    """
    Create a reverse ssh tunnel so one server application can connect to another one.

    Typically, steering_computer creates connection to server1 and server2. However, there
    is no direct link server1-server2 which is needed for Field operations (getField, setField).
    Assume a working connection server1-steering_computer on NAT port 6000. This function creates
    a tunnel steering_computer:6000 and server2:7000 so server2 has direct access to server1's data.

           steering_computer
            /              \
    from server1:6000     to server2:7000


    :param SSHContext fromContext: Remote application
    :param Model.Model fromApplication: Application object from which we want to create a tunnel
    :param Model.Model toApplication: Application object to which we want to create a tunnel

    :return: Instance of sshTunnel class
    :rtype: sshTunnel
    """
    uri = toApplication.getURI()
    natPort = getNATfromUri( uri )
    uri = fromApplication.getURI()
    fromNatPort = natPort #getNATfromUri( uri )
    
    tunnel = sshTunnel(remoteHost='127.0.0.1', userName=fromContext.userName, localPort=natPort, remotePort=fromNatPort, sshClient=fromContext.sshClient, options=fromContext.options, sshHost=fromContext.sshHost, Reverse=True)
    return tunnel

def getNATfromUri (uri):
    """
    Return NAT port from URI, e.g. return 5555 from string PYRO:obj_b178eed8e1994135adf9864725f1d50f@127.0.0.1:5555

    :param str uri: URI from an object

    :return: NAT port number
    :rtype: int
    """
    return int(re.search('(\d+)$', str(uri)).group(0))

def getIPfromUri (uri):
    """
    Returns IP address of the server hosting given URI, e.g. return 127.0.0.1 from string 
    PYRO:obj_b178eed8e1994135adf9864725f1d50f@127.0.0.1:5555
    :param str uri: URI from an object

    :return: IP address 
    :rtype: string
    """
    match = re.search('\@([\w\.]+)\:\d+$', str(uri))
    if match:
        return match.group(1)
    else:
        log.error("getIPfromUri: uri format mismatch (%s)"%(uri))
        return None

def getObjectFromURI(uri, hkey):
    """
    Returns object from given URI, e.g. returns a field
    :param str uri: URI from an object
    :param str hkey: A password string

    :return: Field, Property etc.
    :rtype: object including hkey
    """
    ret = Pyro4.Proxy(uri)
    ret._pyroHmacKey = hkey.encode(encoding='UTF-8')
    return ret

def getUserInfo ():
    """
    :return: tuple containing (username, hostname)
    :rtype: tuple of strings
    """
    username = getpass.getuser()
    hostname = socket.gethostname()
    return (username, hostname)

def connectJobManager (ns, jobManName, hkey, sshContext=None):
    """
    Connect to jobManager described by given jobManRec and create an optional ssh tunnel

    :param jobManName name under which jobmanager is registered on NS
    :param str hkey: A password string
    :param sshContext describing optional ssh tunnel connection detail 

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: JobManager.RemoteJobManager
    :raises Exception: if creation of a tunnel failed
    """

    (jobManHostname, jobManPort, jobManNatHost, jobManNatport) = getNSConnectionInfo(ns, jobManName)
    log.info('Located Job Manager %s at: %s %s %s %s' % (jobManName, jobManHostname, jobManPort, jobManNatHost, jobManNatport))
    #(jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    #create tunnel to JobManager running on (remote) server
    tunnelJobMan = None
    if sshContext:
        try:
            tunnelJobMan = sshTunnel(remoteHost=jobManHostname, userName=sshContext.userName, localPort=jobManNatport, remotePort=jobManPort,
                                     sshClient=sshContext.sshClient, options=sshContext.options, sshHost=sshContext.sshHost)
        except Exception:
            log.exception('Creating ssh tunnel for JobManager failed for remoteHost %s userName %s localPort %s remotePort %s sshClient %s options %s sshHost %s' % (jobManHostname, sshContext.userName, jobManNatport, jobManPort, sshContext.sshClient, sshContext.options, sshContext.sshHost))
            raise

    # locate remote jobManager on (remote) server
    jobMan = _connectApp(ns, jobManName, hkey)
    #return (jobMan, tunnelJobMan)
    return JobManager.RemoteJobManager(jobMan, tunnelJobMan)


def allocateApplicationWithJobManager (ns, jobMan, natPort, hkey, sshContext=None):
    """
    Request new application instance to be spawned by  given jobManager.
    
    :param Pyro4.naming.Nameserver ns: running name server
    :param jobManager jobManager: jobmanager to use
    :param int natPort: nat port on a local computer for ssh tunnel for the application
    :param str hkey: A password string
    :param sshContext sshContext: describing optional ssh tunnel connection detail

    :returns: Application instance
    :rtype: Model.RemoteModel
    :raises Exception: if allocation of job fails
    
    """

    #(jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    log.debug('Trying to connect to JobManager')
    #(jobMan, tunnelJobMan) = connectJobManager (ns, jobManName, userName, sshClient, options, sshHost)

    #if jobMan is None:
    #   e = OSError("Can not connect to JobManager")
    #   log.exception(e)
    #   raise e
    #else:
    #   log.debug('Connected to JobManager %s using tunnel %s' % (jobMan, tunnelJobMan))

    #if tunnelJobMan is None:
    #   e = OSError("Can not create a ssh tunnel to JobManager")
    #   log.exception(e)
    #   raise

    try:
        (username,hostname)=getUserInfo()
        retRec = jobMan.allocateJob(username+"@"+hostname, natPort=natPort)
        log.info('Allocated job, returned record from jobManager:' +  str(retRec))
    except Exception:
        log.exception("JobManager allocateJob() failed")
        raise

    #create tunnel to application's daemon running on (remote) server
    appTunnel = None
    if sshContext:
        try:
            (jobManHostname, jobManPort, jobManNatHost, jobManNatport) = getNSConnectionInfo(ns, jobMan.getNSName())
            appTunnel = sshTunnel(remoteHost=jobManHostname, userName=sshContext.userName, localPort=natPort, remotePort=retRec[2], sshClient=sshContext.sshClient, options=sshContext.options, sshHost=sshContext.sshHost)
        except Exception:
            log.exception("Creating ssh tunnel for application's daemon failed")
            raise
    else:
        log.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    #time.sleep(1)
    # connect to (remote) application, requests remote proxy
    app = _connectApp(ns, retRec[1], hkey)
    if app==None:
        appTunnel.terminate()
    return Model.RemoteModel(app, jobMan=jobMan, jobID=retRec[1], appTunnel=appTunnel)


def allocateNextApplication (ns, jobMan, natPort, sshContext=None):
    """
    Request new application instance to be spawned by  given jobManager

    :param Pyro4.naming.Nameserver ns: running name server
    :param jobManager jobmanager to use 
    :param int natPort: nat port on a local computer for ssh tunnel for the application
    :param sshContext describing optional ssh tunnel connection detail 

    :returns: Application instance
    :rtype: Model.RemoteModel
    :raises Exception: if allocation of job fails
    """
    return allocateApplicationWithJobManager (ns, jobMan, natPort, sshContext)

from . import PyroFile
def downloadPyroFile (newLocalFileName, pyroFile, compressFlag=False):
    """
    Allows to download remote file (pyro ile handle) to a local file.

    :param str newLocalFileName: path to a new local file on a client.
    :param PyroFile pyroFile: representation of existing remote server's file
    :param bool compressFlag: will activate compression during data transfer (zlib)
    """
    file = PyroFile.PyroFile(newLocalFileName, 'wb')
    if compressFlag:
        pyroFile.setCompressionFlag()
        file.setCompressionFlag()
    data = pyroFile.getChunk() # this is where the potential remote communication via Pyro happen
    while data:
        file.setChunk(data)
        data = pyroFile.getChunk()
    file.setChunk(pyroFile.getTerminalChunk())
    pyroFile.close()
    file.close()


def downloadPyroFileFromServer(newLocalFileName, pyroFile, compressFlag=False):
    """
    See :func:'downloadPyroFileFromServer'
    """
    downloadPyroFile(newLocalFileName, pyroFile, compressFlag)


def uploadPyroFile(clientFileName, pyroFile, hkey, size=1024, compressFlag=False):
    """
    Allows to upload given local file to a remote location (represented by Pyro file hanfdle).

    :param str clientFileName: path to existing local file on a client where we are
    :param PyroFile pyroFile: represenation of remote file, this file will be created
    :param str hkey: A password string
    :param int size: optional chunk size. The data are read and written in byte chunks of this size
    :param bool compressFlag: will activate compression during data transfer (zlib)
    """
    file = PyroFile.PyroFile(clientFileName, 'rb', buffsize=size)
    if compressFlag:
        file.setCompressionFlag()
        pyroFile.setCompressionFlag()
    data = file.getChunk()
    while data:
        pyroFile._pyroHmacKey = hkey.encode(encoding='UTF-8')
        pyroFile.setChunk(data)  # this is where the data are sent over net via Pyro
        data = file.getChunk()
    getTermChunk = file.getTerminalChunk()
    pyroFile.setChunk(getTermChunk.encode(encoding='utf-8'))
    file.close()
    pyroFile.close()

def uploadPyroFileOnServer (clientFileName, pyroFile, size = 1024, compressFlag=False):
    """
    See :func:'downloadPyroFile'
    """
    uploadPyroFile (clientFileName, pyroFile, size, compressFlag)
