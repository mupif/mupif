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
import Pyro5
import socket
import getpass
import subprocess
import threading
import time
from . import model
from . import jobmanager
from . import util
from . import apierror
from . import pyrofile
log = util.setupLogger(fileName=None)

Pyro5.config.SERIALIZER = "serpent"
# some versions of Pyro don't have this attribute... (strange, is documented)
# if hasattr(Pyro5.config, 'PICKLE_PROTOCOL_VERSION'):
#     Pyro5.config.PICKLE_PROTOCOL_VERSION = 2  # use lower version for interoperability between python 2 and 3
# Pyro5.config.SERIALIZERS_ACCEPTED = {'pickle'}
# Pyro4.config.THREADPOOL_SIZE=100
Pyro5.config.SERVERTYPE = "multiplex"

try:
    import importlib.resources as imp_res  # for newer Python versions
except ImportError:
    import importlib_resources as imp_res  # for older Python versions

from contextlib import ExitStack
tmpfile=ExitStack()
import itertools
testSSL=dict([((who,what),str(tmpfile.enter_context(imp_res.path('mupif.data.certs',f'{who}.mupif.{what}')))) for who,what in itertools.product(('rootCA','server','client'),('cert','key'))])


def fixAnyIP(ip,name):
    # origin: https://stackoverflow.com/a/28950776/761090
    '''Guess (non-localhost) IP when binding to '0.0.0.0' (IPv4) or '::' (IPv6)'''
    if ip!='0.0.0.0' or ip!='::': return ip
    ipv4=(ip=='0.0.0.0')
    import socket
    s=socket.socket(socket.AF_INET if ipv4 else socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        # 2001:db8::1234 is TESTNET address
        s.connect(('10.255.255.255' if ipv4 else '2001:db8::1234',1)) 
        ret=s.getsockname()[0]
        log.info(f'IPv{4 if ipv4 else 6} address for {name} adjusted: {ip} → {ret}')
        return ret
    except Exception:
        ret='127.0.0.1' if ipv4 else '::1'
        log.error(f'IPv{4 if ipv4 else 6} address for {name}: adjustment of {ip} failed, returning {ret} (localhost)')
        return ret
    finally:
        s.close()

from dataclasses import dataclass
from typing import Optional, Union
@dataclass
class PyroNetConf:
    nshost: Optional[str]=None
    nsport: int=0
    ns: Optional[Pyro5.api.Proxy]=None
    nathost: Optional[str]=None
    natport: int=0
    host: Optional[str]=None
    port: int=0

    def getNS(self):
        if self.ns is not None: return self.ns
        # self.ns=Pyro5.api.locate_ns(host=self.nshost, port=self.nsport)
        self.ns=connectNameServer(nshost=self.nshost, nsport=self.nsport)
        return self.ns


# pyro5 nameserver metadata
NS_METADATA_jobmanager = "type:jobmanager"
NS_METADATA_appserver = "type:appserver"
NS_METADATA_host = 'host'
NS_METADATA_port = 'port'
NS_METADATA_nathost = 'nathost'
NS_METADATA_natport = 'natport'

import pydantic

@pydantic.validate_arguments
def connectNameServer(nshost: Optional[str]=None, nsport: int=0, timeOut: float=3.0):
    """
    Connects to a NameServer.

    :param str nshost: IP address of nameServer
    :param int nsport: Nameserver port.
    :param float timeOut: Waiting time for response in seconds
    :return: NameServer
    :rtype: Pyro5.naming.Nameserver
    :raises Exception: When can not connect to a LISTENING port of nameserver
    """
    
    if nshost is not None and nsport!=0:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeOut)
            try:  # Treat socket connection problems separately
                s.connect((nshost, nsport))
            except socket.error as msg:
                log.exception(msg)
                raise Exception('Socket connection error to nameServer')
            s.close()
            log.debug("Can connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport))
        except Exception:
            msg = "Can not connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport) + \
                  ". Does a firewall block INPUT or OUTPUT on the port? Exiting."
            log.exception(msg)
            raise

    # locate nameserver
    try:
        ns = Pyro5.api.locate_ns(host=nshost, port=int(nsport))
        log.debug(f"Connected to NameServer on {nshost}:{nsport}. Pyro5 version on your localhost is {Pyro5.__version__}.")
    except Exception:
        log.exception(f"Can not connect to NameServer on {nshost}:{nsport}. Is the NameServer running? Runs the NameServer on the same Pyro version as this version {Pyro5.__version__}? Exiting.")
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
    host = None
    port = None
    nathost = None
    natport = None
    
    for i in mdata:
        match = re.search('\A'+NS_METADATA_host+':([\w\.]+)', i)
        if match:
            host = match.group(1)
        match = re.search('\A'+NS_METADATA_port+':(\w+)', i)
        if match:
            port = int(match.group(1))
        match = re.search('\A'+NS_METADATA_nathost+':([\w\.]+)', i)
        if match:
            nathost = match.group(1)
        match = re.search('\A'+NS_METADATA_natport+':(\w+)', i)
        if match:
            natport = match.group(1)
        
    return (host, port, nathost, natport)
            

def _connectApp(ns, name, connectionTestTimeOut = 10. ):
    """
    Connects to a remote application.

    :param Pyro5.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :param connectionTestTimeOut timeout for connection test
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application or Timeout passes
    """
    try:
        uri = ns.lookup(name)
        log.debug("Application %s, found URI %s on %s from a nameServer %s" % (
            name, uri, getNSConnectionInfo(ns, name), ns))
        app2 = Pyro5.api.Proxy(uri)
    except Exception as e:
        log.error("Cannot find registered server %s on %s" % (name, ns) )
        raise

    try:
        log.info("Connecting to application %s with %s"%(name, app2))
        # By default, Pyro waits an indefinite amount of time for the call to return. 
        # When testing connection to an remote object via _connectApp, the object getSignature method is called.
        # The connection timeout is set for this call. after this, the timeout is reset to default.
        # When timeout is passed, Pyro4.errors.CommunicationError is thrown.
        # This is essential to detect the case when, for example, object has been registered at namesever, 
        # but is not operational at the moment.
        app2._pyroTimeout = connectionTestTimeOut
        sig = app2.getApplicationSignature()
        app2._pyroTimeout = None
        log.debug("Connected to " + sig + " with the application " + name)
    except Pyro5.core.errors.CommunicationError as e:
        log.error("Communication error, perhaps SSL issue?")
        raise
    except Exception as e:
        log.exception("Cannot connect to application " + name + ". Is the server running?")
        raise

    return app2


def connectApp(ns, name, sshContext=None, connectionTestTimeOut = 10.):
    """
    Connects to a remote application, creates the ssh tunnel if necessary

    :param Pyro5.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :param sshContext:
    :return: Application Decorator (docorating pyro proxy with ssh tunnel instance)
    :rtype: Instance of an application decorator
    :raises Exception: When cannot find registered server or Cannot connect to application
    """
    tunnel = None
    if sshContext:
        (hostname, port, natHost, natport) = getNSConnectionInfo(ns, name)
        try:
            tunnel = SshTunnel(remoteHost=hostname, userName=sshContext.userName, localPort=natport, remotePort=port,
                               sshClient=sshContext.sshClient, options=sshContext.options, sshHost=sshContext.sshHost)
        except Exception:
            log.exception(
                'Creating ssh tunnel failed for remoteHost %s userName %s localPort %s remotePort %s sshClient %s '
                'options %s sshHost %s' % (
                    hostname, sshContext.userName, natport, port, sshContext.sshClient, sshContext.options,
                    sshContext.sshHost)
            )
            raise

    app = _connectApp(ns, name, connectionTestTimeOut)
    return model.RemoteModel(app, appTunnel=tunnel)


def getNSAppName(jobname, appname):
    """
    Get application name.

    :param str jobname: Arbitrary string concatenated in the outut
    :param str appname: Arbitrary string concatenated in the outut
    :return: String of concatenated arguments
    :rtype: str
    """
    return 'Mupif'+'.'+jobname+'.'+appname


def runDaemon(host, port, nathost=None, natport=None):
    """
    Runs a daemon without registering to a name server
    :param str(int) host: Host name where daemon runs. This is typically a localhost
    :param int or tuple port: Port number where daemon will listen (internal port number) or tuple of possible ports
    :param str(int) nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port, optional (external port)

    :return Instance of the running daemon, None if a problem
    :rtype Pyro5.api.Daemon
    """
    host=fixAnyIP(host,'[daemon]')
    if isinstance(port, (tuple, list)):
        ports = port
    else:
        ports = (port,)

    for iport in ports:
        try:
            daemon = Pyro5.api.Daemon(host=host, port=int(iport), nathost=nathost, natport=util.NoneOrInt(natport))
            log.info('Pyro5 daemon runs on %s:%s using nathost %s:%s' % (host, iport, nathost, natport))
            return daemon
        except socket.error as e:
            log.debug('Socket port %s:%s seems to be already in use' % (host, iport))
            daemon = None
        except Exception:
            log.exception('Can not run Pyro5 daemon on %s:%s using nathost %s:%s' % (host, iport, nathost, natport))
            daemon = None
    
    raise apierror.APIError('Can not run Pyro5 daemon on configured ports')


def runServer(net: PyroNetConf, appName, app, daemon=None, metadata=None):
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
    :param daemon: Reference to already running daemon, if available. Optional parameter.
    :param metadata: set of strings that will be the metadata tags associated with the object registration. See pyroutil.py for valid tags. The metadata string "connection:server:port:nathost:natport" will be automatically generated.

    :raises Exception: if can not run Pyro5 daemon
    :returns: URI
    """
    # server, port, nathost, natport, nshost, nsport, 
    # fix the IP address published so that it is not 0.0.0.0
    host=fixAnyIP(net.host,appName)

    externalDaemon = False
    if not daemon:
        try:
            daemon = Pyro5.api.Daemon(host=host,port=net.port,nathost=net.nathost,natport=net.natport)
            log.info(f'Pyro5 daemon runs on {host}:{net.port} using nathost {net.nathost}:{net.natport}')
        except Exception:
            log.exception(f'Can not run Pyro5 daemon on {host}:{net.port} using nathost {net.nathost}:{net.natport}')
            raise
    else:
        externalDaemon = True

    ns=net.getNS()
    # Check if application name already exists on a nameServer
    try:
        (uri, mdata) = ns.lookup(appName, return_metadata=True)
    except Pyro5.core.errors.NamingError:
        pass
    else:
        log.warning(f'Application name {appName} is already registered on name server, overwriting.')
    
    uri = daemon.register(app)
    try:
        app.registerPyro(daemon, ns, uri, appName, externalDaemon=externalDaemon)
    except AttributeError as e:
        # catch attribute error (thrown when method not defined)
        log.warning(f'Can not register daemon for application {appName}')
    except:
        log.exception(f'Can not register daemon on {host}:{net.port} using nathost {net.nathost}:{net.natport} on nameServer')
        raise

    # generate connection metadata entry
    metadata.add('%s:%s' % (NS_METADATA_host, host))
    metadata.add('%s:%s' % (NS_METADATA_port, net.port))
    metadata.add('%s:%s' % (NS_METADATA_nathost, net.nathost))
    metadata.add('%s:%s' % (NS_METADATA_natport, net.natport))
    ns.register(appName, uri, metadata=metadata)

    log.debug('NameServer %s has registered uri %s' % (appName, uri))
    log.debug(f'Running runServer: server:{host}, port:{net.port}, nathost:{net.nathost}, natport:{net.natport}, nameServer:{net.nshost}, nameServerPort:{net.nsport}: applicationName:{appName}, daemon URI {uri}')
    threading.Thread(target=daemon.requestLoop).start() # run daemon request loop in separate thread
    return uri


def runAppServer(server, port, nathost, natport, nshost, nsport, appName, app, daemon=None):
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
    :param daemon: Reference to already running daemon, if available. Optional parameter.

    :raises Exception: if can not run Pyro5 daemon
    """
    return runServer(
        net=PyroNetConf(host=server,port=port,nathost=nathost,natport=natport,nshost=nshost,nsport=nsport),
        appName=appName,
        app=app,
        daemon=daemon,
        metadata={NS_METADATA_appserver}
    )


def runJobManagerServer(server, port, nathost, natport, nshost, nsport, appName, jobman, daemon=None):
    """
    Registers and runs given jobManager server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str appName: Name of job manager to be registered at nameserver
    :param jobman: Jobmanager
    :param daemon: Reference to already running daemon, if available. Optional parameter.
    """
    return runServer(
        net=PyroNetConf(host=server,port=port,nathost=nathost,natport=natport,nshost=nshost,nsport=nsport),
        appName=appName,
        app=jobman,
        daemon=daemon,
        metadata={NS_METADATA_jobmanager}
    )


# def connectApplicationsViaClient(fromSolverAppRec, toApplication, sshClient='ssh', options=''):
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
    :param model.Model or model.RemoteModel fromApplication: Application object from which we want to create a tunnel
    :param model.Model or model.RemoteModel toApplication: Application object to which we want to create a tunnel

    :return: Instance of SshTunnel class
    :rtype: SshTunnel
    """
    uri = toApplication.getURI()
    natPort = getNATfromUri(uri)
    # uri = fromApplication.getURI()
    fromNatPort = natPort  # getNATfromUri( uri )
    
    tunnel = SshTunnel(
        remoteHost='127.0.0.1', userName=fromContext.userName, localPort=natPort, remotePort=fromNatPort,
        sshClient=fromContext.sshClient, options=fromContext.options, sshHost=fromContext.sshHost, Reverse=True)
    return tunnel


def getNATfromUri(uri):
    """
    Return NAT port from URI, e.g. return 5555 from string PYRO:obj_b178eed8e1994135adf9864725f1d50f@127.0.0.1:5555

    :param str uri: URI from an object

    :return: NAT port number
    :rtype: int
    """
    return int(re.search('(\d+)$', str(uri)).group(0))


def getIPfromUri(uri):
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
        log.error("getIPfromUri: uri format mismatch (%s)" % uri)
        return None


def getObjectFromURI(uri):
    """
    Returns object from given URI, e.g. returns a field
    :param str uri: URI from an object

    :return: Field, Property etc.
    :rtype: object
    """
    ret = Pyro5.api.Proxy(uri)
    return ret


def getUserInfo():
    """
    :return: tuple containing (username, hostname)
    :rtype: tuple of strings
    """
    username = getpass.getuser()
    hostname = socket.gethostname()
    return username, hostname


def connectJobManager(ns, jobManName, sshContext=None):
    """
    Connect to jobManager described by given jobManRec and create an optional ssh tunnel

    :param jobManName name under which jobmanager is registered on NS
    :param sshContext describing optional ssh tunnel connection detail 

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: jobmanager.RemoteJobManager
    :raises Exception: if creation of a tunnel failed
    """

    (jobManHostname, jobManPort, jobManNatHost, jobManNatport) = getNSConnectionInfo(ns, jobManName)
    log.info('Located Job Manager %s at: %s %s %s %s' % (
        jobManName, jobManHostname, jobManPort, jobManNatHost, jobManNatport))
    # (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    # create tunnel to JobManager running on (remote) server
    tunnelJobMan = None
    if sshContext:
        try:
            tunnelJobMan = SshTunnel(
                remoteHost=jobManHostname, userName=sshContext.userName, localPort=jobManNatport, remotePort=jobManPort,
                sshClient=sshContext.sshClient, options=sshContext.options, sshHost=sshContext.sshHost)
        except Exception:
            log.exception(
                'Creating ssh tunnel for JobManager failed for remoteHost %s userName %s localPort %s remotePort %s '
                'sshClient %s options %s sshHost %s' % (
                    jobManHostname, sshContext.userName, jobManNatport, jobManPort, sshContext.sshClient,
                    sshContext.options, sshContext.sshHost
                )
            )
            raise

    # locate remote jobManager on (remote) server
    jobMan = _connectApp(ns, jobManName)
    # return (jobMan, tunnelJobMan)
    return jobmanager.RemoteJobManager(jobMan, tunnelJobMan)


def allocateApplicationWithJobManager(ns, jobMan, natPort, sshContext=None):
    """
    Request new application instance to be spawned by  given jobManager.
    
    :param Pyro5.naming.Nameserver ns: running name server
    :param jobManager jobMan: jobmanager to use
    :param int natPort: nat port on a local computer for ssh tunnel for the application
    :param sshContext sshContext: describing optional ssh tunnel connection detail

    :returns: Application instance
    :rtype: model.RemoteModel
    :raises Exception: if allocation of job fails
    """

    # (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    log.debug('Trying to connect to JobManager')
    # (jobMan, tunnelJobMan) = connectJobManager (ns, jobManName, userName, sshClient, options, sshHost)

    # if jobMan is None:
    #     e = OSError("Can not connect to JobManager")
    #     log.exception(e)
    #     raise e
    # else:
    #     log.debug('Connected to JobManager %s using tunnel %s' % (jobMan, tunnelJobMan))

    # if tunnelJobMan is None:
    #     e = OSError("Can not create a ssh tunnel to JobManager")
    #     log.exception(e)
    #     raise

    try:
        (username, hostname) = getUserInfo()
        retRec = jobMan.allocateJob(username+"@"+hostname, natPort=natPort)
        log.info('Allocated job, returned record from jobManager:' + str(retRec))
    except Exception:
        log.exception("JobManager allocateJob() failed")
        print("".join(Pyro5.errors.get_pyro_traceback()))
        raise

    # create tunnel to application's daemon running on (remote) server
    appTunnel = None
    if sshContext:
        try:
            (jobManHostname, jobManPort, jobManNatHost, jobManNatport) = getNSConnectionInfo(ns, jobMan.getNSName())
            appTunnel = SshTunnel(
                remoteHost=jobManHostname,
                userName=sshContext.userName,
                localPort=natPort,
                remotePort=retRec[2],
                sshClient=sshContext.sshClient,
                options=sshContext.options,
                sshHost=sshContext.sshHost
            )
        except Exception:
            log.exception("Creating ssh tunnel for application's daemon failed")
            raise
    else:
        log.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    # time.sleep(1)
    # connect to (remote) application, requests remote proxy
    app = _connectApp(ns, retRec[1])
    if app is None:
        appTunnel.terminate()
    return model.RemoteModel(app, jobMan=jobMan, jobID=retRec[1], appTunnel=appTunnel)


def allocateNextApplication(ns, jobMan, natPort, sshContext=None):
    """
    Request a new application instance to be spawned by given jobManager
    
    :param Pyro5.naming.Nameserver ns: running name server
    :param jobMan: jobmanager to use
    :param int natPort: nat port on a local computer for ssh tunnel for the application
    :param sshContext: describing optional ssh tunnel connection detail
    
    :return: Application instance
    :rtype: model.RemoteModel
    :raises Exception: if allocation of job fails
    """
    return allocateApplicationWithJobManager(ns, jobMan, natPort, sshContext)


def downloadPyroFile(newLocalFileName, pyroFile, compressFlag=True):
    """
    Allows to download remote file (pyro file handle) to a local file.

    :param str newLocalFileName: path to a new local file on a client.
    :param pyrofile.PyroFile pyroFile: representation of existing remote server's file
    :param bool compressFlag: will activate compression during data transfer (zlib)
    """
    file = pyrofile.PyroFile(newLocalFileName, 'wb', compressFlag=compressFlag)
    if compressFlag:
        pyroFile.setCompressionFlag()
        file.setCompressionFlag()
    data = pyroFile.getChunk()  # this is where the potential remote communication via Pyro happen
    while data:
        file.setChunk(data)
        data = pyroFile.getChunk()
    file.setChunk(pyroFile.getTerminalChunk())
    pyroFile.close()
    file.close()


def downloadPyroFileFromServer(newLocalFileName, pyroFile, compressFlag=True):
    """
    See :func:'downloadPyroFileFromServer'
    """
    downloadPyroFile(newLocalFileName, pyroFile, compressFlag)


def uploadPyroFile(clientFileName, pyroFile, size=1024*1024, compressFlag=True):
    """
    Allows to upload given local file to a remote location (represented by Pyro file hanfdle).

    :param str clientFileName: path to existing local file on a client where we are
    :param pyrofile.PyroFile pyroFile: represenation of remote file, this file will be created
    :param int size: optional chunk size. The data are read and written in byte chunks of this size
    :param bool compressFlag: will activate compression during data transfer (zlib)
    """
    file = pyrofile.PyroFile(clientFileName, 'rb', buffsize=size, compressFlag=compressFlag)
    log.info("Uploading %s", clientFileName)
    if compressFlag:
        file.setCompressionFlag()
        pyroFile.setCompressionFlag()
        log.info("Setting compression flag on")
    data = file.getChunk()
    while data:
        pyroFile.setChunk(data)  # this is where the data are sent over net via Pyro
        data = file.getChunk()
    getTermChunk = file.getTerminalChunk()
    pyroFile.setChunk(getTermChunk)
    log.info("File transfer finished")
    file.close()
    pyroFile.close()


def uploadPyroFileOnServer(clientFileName, pyroFile, size=1024*1024, compressFlag=True):
    """
    See :func:'downloadPyroFile'
    """
    uploadPyroFile(clientFileName, pyroFile, size, compressFlag)





def useTestSSL():
    '''
    Set Pyro5 SSL test configuration as Pyro5.config. Not to be used in production settings.
    '''
    Pyro5.config.SSL=True
    Pyro5.config.SSL_REQUIRECLIENTCERT=True
    Pyro5.config.SSL_SERVERCERT=testSSL['server','cert']
    Pyro5.config.SSL_SERVERKEY=testSSL['server','key']
    Pyro5.config.SSL_CLIENTCERT=testSSL['client','cert']
    Pyro5.config.SSL_CLIENTKEY=testSSL['client','key']
    Pyro5.config.SSL_CACERTS=testSSL['rootCA','cert']

def useTestSSL_env(e):
    '''
    Set Pyro5 SSL test configuration as environment variables. Not to be used in production settings.
    '''
    e['PYRO_SSL']='1'
    e['PYRO_SSL_REQUIRECLIENTCERT']='1'
    e['PYRO_SSL_SERVERCERT']=testSSL['server','cert']
    e['PYRO_SSL_SERVERKEY']=testSSL['server','key']
    e['PYRO_SSL_CLIENTCERT']=testSSL['client','cert']
    e['PYRO_SSL_CLIENTKEY']=testSSL['client','key']
    e['PYRO_SSL_CACERTS']=testSSL['rootCA','cert']

@dataclass
class SSHContext(object):
    """
    Helper class to store ssh tunnel connection details. It is parameter to different methods (connectJobManager,
    allocateApplicationWithJobManager, etc.).
    When provided, the corresponding ssh tunnel connection is established and associated to proxy using decorator class
    to make sure it can be terminated properly.
    """
    userName: str=''
    sshClient: str='manual'
    options: str=''
    sshHost: str=''
        

class SshTunnel(object):
    """
    Helper class to represent established ssh tunnel. It defines terminate and __del__ method
    to ensure correct tunnel termination.
    """

    async def runAsyncSSH(self,fwd,**kw):
        'Async function which just creates background asyncssh task (tunnel) and returns'
        async def _go():
            'Create asyncssh connection and local/remote forwarding tunnel'
            import asyncssh
            async with asyncssh.connect(**kw) as conn:
                direction,localPort,remoteHost,remotePort=fwd
                if direction=='L': listener=await conn.forward_local_port('',localPort,remoteHost,remotePort)
                else: listener=await conn.forward_remote_port('',remotePort,'localhost',localPort)
                await listener.wait_closed()
        import asyncio
        asyncio.create_task(_go())

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

        if sshHost == '':
            sshHost = remoteHost
        if userName == '':
            userName = os.getenv('USER')
                
        direction = 'L'
        if Reverse is True:
            direction = 'R'

        self.sshClient=sshClient
        self.tunnel=None

        if sshClient == 'asyncssh':
            # try to convert OpenSSH arguments to asyncssh options
            import argparse
            parser=argparse.ArgumentParser(add_help=False)
            parser.add_argument('-F',dest='config')
            parser.add_argument('-p',type=int,dest='ssh_port')
            parser.add_argument('-oIdentityFile',type=str,action='append',dest='client_keys')
            parser.add_argument('-oUserKnownHostsFile',type=str,dest='known_hosts')
            parser.add_argument('-N',action='store_true')
            kwopts=vars(parser.parse_args(options.split()))
            port=kwopts.pop('ssh_port',22)
            log.info('Options extracted from OpenSSH command-line: '+str(kwopts))
            kwopts.pop('N',None) # not useful
            import asyncio
            asyncio.run(self.runAsyncSSH(fwd=(direction,localPort,remoteHost,remotePort),host=remoteHost,port=remotePort,**kwopts))
        elif sshClient == 'manual':
            # You need ssh server running, e.g. UNIX-sshd or WIN-freesshd
            print(direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            cmd1 = 'ssh -%s %s:%s:%s %s@%s -N %s' % (
                direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            cmd2 = 'putty.exe -%s %s:%s:%s %s@%s -N %s' % (
                direction, localPort, remoteHost, remotePort, userName, sshHost, options)
            log.info("If ssh tunnel does not exist and you need it, do it manually using a command e.g. " + cmd1 +
                     " , or " + cmd2)
        else:
            # command-based clients, create self.tunnel as process which can be terminated

            # use direct system command. Paramiko or sshtunnel do not work.
            # put ssh public key on a server - interaction with a keyboard
            # for password will not work here (password goes through TTY, not stdin)
            if sshClient == 'ssh': cmd0 = 'ssh'
            elif sshClient == 'autossh': cmd0 = 'autossh'
            elif 'putty' in sshClient.lower(): cmd0=sshClient
            else: raise ValueError('Unknown ssh client {sshClient}.')
            # for putty:
            # need to create a public key *.ppk using puttygen.
            # It can be created by importing Linux private key.
            # The path to that key is given as -i option
            cmd = [cmd0,f'-{direction}',f'{localPort}:{remoteHost}:{remotePort}',f'{userName}@{sshHost}','-N',options]

            try:
                log.debug("Creating ssh tunnel via command: " + str(cmd))
                self.tunnel = subprocess.Popen(cmd.split())
            except Exception:
                log.exception("Creation of a tunnel failed. Can not execute the command: %s " % str(cmd))
                raise

        time.sleep(1.0)

    def terminate(self):
        """
        Terminate the connection.
        """
        if self.tunnel is not None:
            if self.sshCient=='python':
                self.tunnel.cancel()
                self.tunnel=None
            else:
                self.tunnel.terminate()
                self.tunnel = None

    def __del__(self):
        self.terminate()


