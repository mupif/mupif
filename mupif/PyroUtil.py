from __future__ import absolute_import
from builtins import str
import os
import re
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
#
#import logging - logger moved to __init__.py
#formatLog = '%(asctime)s %(levelname)s:%(filename)s:%(lineno)d %(message)s \n'
#formatTime = '%Y-%m-%d %H:%M:%S'
#logging.basicConfig(filename='mupif.log',filemode='w',format=formatLog,level=logging.DEBUG)
#logger = logging.getLogger()#create a logger
#ch = logging.StreamHandler()
#ch.setFormatter(logging.Formatter(formatLog, formatTime))
#logger.addHandler(ch)

import Pyro4
import socket
import getpass
import subprocess
import time
from . import RemoteAppRecord
from mupif import log

Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}

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
        s.connect((nshost, nsport))
        s.close()
        log.debug("Can connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport))
    except Exception:
        msg = "Can not connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport) + ". Does a firewall block INPUT or OUTPUT on the port? Exiting."
        log.exception(msg)
        raise

    #locate nameserver
    try:
        ns = Pyro4.locateNS(host=nshost, port=nsport,hmac_key=hkey)
        msg = "Connected to NameServer on %s:%s. Pyro4 version on your localhost is %s" %(nshost, nsport, Pyro4.constants.VERSION)
        log.debug(msg)
    except Exception:
        msg = "Can not connect to NameServer on %s:%s. Is the NameServer running? Runs the NameServer on the same Pyro version as this version %s? Do you have the correct hmac_key (password is now %s)? Exiting." %(nshost, nsport, Pyro4.constants.VERSION, hkey)
        log.exception(msg)
        raise

    return ns


def connectApp(ns, name):
    """
    Connects to a remote application.

    :param Pyro4.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application
    """
    try:
        uri = ns.lookup(name)
        log.debug("Found URI %s from a nameServer %s" % (uri, ns) )
        app2 = Pyro4.Proxy(uri)
    except Exception as e:
        log.error("Cannot find registered server %s on %s" % (name, ns) )
        raise

    try:
        sig = app2.getApplicationSignature()
        log.debug("Connected to " + sig + " with the name " + name)
    except Exception as e:
        log.exception("Cannot connect to application " + name + ". Is the server running?")
        raise

    return app2


def getNSAppName(jobname, appname):
    """
    Get application name.

    :param str jobname: Arbitrary string concatenated in the outut
    :param str appname: Arbitrary string concatenated in the outut
    :return: String of concatenated arguments
    :rtype: str
    """
    return 'Mupif'+'.'+jobname+'.'+appname

def runDaemon(host, port, nathost, natport):
    """
    Runs a daemon without geristering to a name server
    :param str(int) host: Host name where daemon runs. This is typically a localhost
    :param int port: Port number where daemon will listen (internal port number)
    :param str(int) nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port, optional (external port)

    :return Instance of the running daemon, None if a problem
    :rtype Pyro4.Daemon 
    """
    try:
        daemon = Pyro4.Daemon(host=host, port=port, nathost=nathost, natport=natport)
        log.info('Pyro4 daemon runs on %s:%d using nathost %s:%d' % (host, port, nathost, natport))
    except socket.error as e:
        log.debug('Socket port %s:%d seems to be already in use' % (host,port))
        daemon = None
        raise e

    except Exception:
        log.exception('Can not run Pyro4 daemon on %s:%d using nathost %s:%d' % (host, port, nathost, natport))
        daemon = None
        raise

    return daemon

def runAppServer(server, port, nathost, natport, nshost, nsport, nsname, hkey, app, daemon=None):
    """
    Runs a simple application server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str nsname: Name of registered application
    :param str hkey: A password string
    :param instance app: Application instance
    :param daemon: Reference to already running daemon, if available. Optional parameter.

    :raises Exception: if can not run Pyro4 daemon
    """
    externalDaemon = False
    if not daemon:
        try:
            daemon = Pyro4.Daemon(host=server, port=port, nathost=nathost, natport=natport)
            log.info('Pyro4 daemon runs on %s:%d using nathost %s:%d and hkey %s' % (server, port, nathost, natport, hkey))
        except Exception:
            log.exception('Can not run Pyro4 daemon on %s:%d using nathost %s:%d  and hmac %s' % (server, port, nathost, natport, hkey))
            raise
            exit(1)
    else:
        externalDaemon = True

    ns = connectNameServer(nshost, nsport, hkey)
    #register agent
    uri = daemon.register(app)
    ns.register(nsname, uri)
    app.registerPyro(daemon, ns, uri, externalDaemon=externalDaemon)

    log.debug('NameServer %s has registered uri %s' % (nsname, uri) )
    log.debug('Running runAppServer: server:%s, port:%d, nathost:%s, natport:%d, nameServer:%s, nameServerPort:%d, applicationName:%s, daemon URI %s' % (server, port, nathost, natport, nshost, nsport, nsname, uri) )
    daemon.requestLoop()


def sshTunnel(remoteHost, userName, localPort, remotePort, sshClient='ssh', options='', sshHost='', Reverse=False):
    """
    Automatic creation of ssh tunnel, using putty.exe for Windows and ssh for Linux

    :param str remoteHost: IP of remote host
    :param str userName: User name, if empty, current user name is used
    :param int localPort: Local port
    :param int remotePort: Remote port
    :param str sshClient: Path to executable ssh client (on Windows use double backslashes 'C:\\Program Files\\Putty\putty.exe')
    :param str options: Arguments to ssh clinent, e.g. the location of private ssh keys
    :param str sshHost: Computer used for tunelling, optional. If empty, equals to remoteHost
    :param bool Reverse: True if reverse tunnel to be created (default is False)

    :return: Instance of subprocess.Popen running the tunneling command
    :rtype: subprocess.Popen
    :raises Exception: if creation of a tunnel failed
    """

    if sshHost =='':
        sshHost = remoteHost
    if userName =='':
        userName = os.getlogin()

    direction = 'L'
    if Reverse == True:
        direction = 'R'

    #use direct system command. Paramiko or sshtunnel do not work.
    #put ssh public key on a server - interaction with a keyboard for password will not work here (password goes through TTY, not stdin)
    if sshClient=='ssh':
        cmd = 'ssh -%s %d:%s:%d %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
        log.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='autossh':
        cmd = 'autossh -%s %d:%s:%d %s@%s -N %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
        log.debug("Creating autossh tunnel via command: " + cmd)
    elif 'putty' in sshClient.lower():
        #need to create a public key *.ppk using puttygen. It can be created by importing Linux private key. The path to that key is given as -i option
        cmd = '%s -%s %d:%s:%d %s@%s -N %s' % (sshClient, direction, localPort, remoteHost, remotePort, userName, sshHost, options)
        log.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='manual':
        #You need ssh server running, e.g. UNIX-sshd or WIN-freesshd
        cmd1 = 'ssh -%s %d:%s:%d %s@%s' % (direction, localPort, remoteHost, remotePort, userName, sshHost)
        cmd2 = 'putty.exe -%s %d:%s:%d %s@%s %s' % (direction, localPort, remoteHost, remotePort, userName, sshHost, options)
        log.info("If ssh tunnel does not exist, do it manually using a command e.g. " + cmd1 + " , or " + cmd2)
        return None
    else:
        log.error("Unknown ssh client, exiting")
        exit(0)
    try:
        tunnel = subprocess.Popen(cmd.split())
    except Exception:
        log.exception("Creation of a tunnel failed. Can not execute the command: %s " % cmd)
        raise

    time.sleep(1.0)

    return tunnel 

def connectApplicationsViaClient(fromSolverAppRec, toApplication, sshClient='ssh', options=''):
    """
    Create a reverse ssh tunnel so one server application can connect to another one.
    
    Typically, steering_computer creates connection to server1 and server2. However, there
    is no direct link server1-server2 which is needed for Field operations (getField, setField).
    Assume a working connection server1-steering_computer on NAT port 6000. This function creates
    a tunnel steering_computer:6000 and server2:6000 so server2 has direct access to server1's data.

        steering_computer
          /           \
    server1          server2


    :param tuple fromSolverAppRec: A tuple defining userName, sshHost
    :param Application toApplication: Application object to which we want to create a tunnel
    :param str sshClient: Path to executable ssh client (on Windows use double backslashes 'C:\\Program Files\\Putty\putty.exe')
    :param str options: Arguments to ssh clinent, e.g. the location of private ssh keys
    
    :return: Instance of subprocess.Popen running the tunneling command
    :rtype: subprocess.Popen
    """
    uri = toApplication.getURI()
    natPort = getNATfromUri( uri )
    tunnel = sshTunnel(remoteHost='127.0.0.1', userName=fromSolverAppRec[3], localPort=natPort, remotePort=natPort, sshClient=sshClient, options=options, sshHost=fromSolverAppRec[2], Reverse=True)
    return tunnel

def getNATfromUri (uri):
    """
    Return NAT port from URI, e.g. return 5555 from string PYRO:obj_b178eed8e1994135adf9864725f1d50f@127.0.0.1:5555

    :param str uri: URI from an object

    :return: NAT port number
    :rtype: int
    """
    return int(re.search('(\d+)$', str(uri)).group(0))


def getUserInfo ():
    """
    :return: String assembled from username+"@"+hostname
    :rtype: str
    """
    username = getpass.getuser()
    hostname = socket.gethostname()
    return username+"@"+hostname

def connectJobManager (ns, jobManRec, sshClient='ssh', options='', sshHost=''):
    """
    Connect to jobManager described by given jobManRec and create a ssh tunnel

    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see client-conf.py
    :param str sshClient: client for ssh tunnel, see :func:`sshTunnel`, default 'ssh'
    :param str options: parameters for ssh tunnel, see :func:`sshTunnel`, default ''
    :param str sshHost: parameters for ssh tunnel, see :func:`sshTunnel`, default ''

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: tuple (JobManager, subprocess.Popen)
    :raises Exception: if creation of a tunnel failed
    """    

    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    #create tunnel to JobManager running on (remote) server
    try:
        tunnelJobMan = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=jobManNatport, remotePort=jobManPort, sshClient=sshClient, options=options, sshHost=sshHost)
    except Exception:
        log.exception("Creating ssh tunnel for JobManager failed")
        raise
    else:
        # locate remote jobManager on (remote) server
        jobMan = connectApp(ns, jobManName)
        return (jobMan, tunnelJobMan)


def allocateApplicationWithJobManager (ns, jobManRec, natPort, sshClient='ssh', options='', sshHost=''):
    """
    Connect to jobManager described by given jobManRec

    :param Pyro4.naming.Nameserver ns: running name server
    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see clientConfig.py
    :param int natPort: nat port in local computer for ssh tunnel for the application
    :param str sshClient: client for ssh tunnel, see :func:`sshTunnel`, default 'ssh'
    :param str options: parameters for ssh tunnel, see :func:`sshTunnel`, default ''
    :param str sshHost: parameters for ssh tunnel, see :func:`sshTunnel`, default ''

    :return: RemoteAppRecord containing application, tunnel to application, tunnel to jobman, jobid
    :rtype: RemoteAppRecord
    :raises Exception: if allocation of job fails
    """
    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    (jobMan, tunnelJobMan) = connectJobManager (ns, jobManRec, sshClient, options, sshHost)

    if jobMan is None:
       e = OSError("Can not connect to JobManager")
       log.exception(e)
       raise e
    else:
       log.debug('Connected to JobManager %s using tunnel %s' % (jobMan, tunnelJobMan))

    if tunnelJobMan is None:
       e = OSError("Can not create a ssh tunnel to JobManager")
       log.exception(e)
       raise

    try:
        retRec = jobMan.allocateJob(getUserInfo(), natPort=natPort)
        log.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception:
        log.exception("JobManager allocateJob() failed")
        raise 

    #create tunnel to application's daemon running on (remote) server
    try:
        tunnelApp = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=natPort, remotePort=retRec[2], sshClient=sshClient, options=options, sshHost=sshHost)
    except Exception:
        log.exception("Creating ssh tunnel for application's daemon failed")
        raise
    else:
        log.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    #time.sleep(1)
    # connect to (remote) application, requests remote proxy
    app = connectApp(ns, retRec[1])
    if app==None:
        tunnelApp.terminate()
    return RemoteAppRecord.RemoteAppRecord(app, tunnelApp, jobMan, tunnelJobMan, retRec[1])


def allocateNextApplication (ns, jobManRec, natPort, appRec, sshClient='ssh', options='', sshHost=''):
    """
    Allocate next application instance on a running Job Manager and adds it into
    existing applicationRecord. 

    :param Pyro4.naming.Nameserver ns: running name server
    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see clientConfig.py
    :param int natPort: nat port in local computer for ssh tunnel for the application
    :param RemoteAppRecord appRec: existing RemoteAppRecord where a new application will be added
    :param str sshClient: client for ssh tunnel, see :func:`sshTunnel`, default 'ssh'
    :param str options: parameters for ssh tunnel, see :func:`sshTunnel`, default ''
    :param str sshHost: parameters for ssh tunnel, see :func:`sshTunnel`, default ''

    :return: None
    :raises Exception: if allocation of job fails
    :raises Exception: if ssh tunnel to application instance can not be created
    """
    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    jobMan = connectApp(ns, jobManName)

    try:
        retRec = jobMan.allocateJob(getUserInfo(), natPort=natPort)
        log.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception:
        log.exception("jobMan.allocateJob() failed")
        raise 

    #create tunnel to application's daemon running on (remote) server
    try:
        tunnelApp = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=natPort, remotePort=retRec[2], sshClient=sshClient, options=options, sshHost=sshHost)
    except Exception:
        log.exception("Creating ssh tunnel for application's daemon failed")
        raise 
    else:
        log.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    app = connectApp(ns, retRec[1])
    if app==None:
        tunnelApp.terminate()
    appRec.appendNextApplication(app,tunnelApp,retRec[1])

from . import PyroFile
def uploadPyroFile (newLocalFileName, pyroFile):
    """
    Allows to upload remote file (pyro ile handle) to a local file.

    :param str newLocalFileName: path to a new local file on a client.
    :param PyroFile pyroFile: representation of existing remote server's file
    """
    file = open (newLocalFileName, 'wb')
    data = pyroFile.getChunk()
    while data:
        file.write(data)
        data = pyroFile.getChunk()
    pyroFile.close()
    file.close()

def uploadPyroFileFromServer (newLocalFileName, pyroFile):
    """
    See :func:'uploadPyroFileFromServer'
    """
    uploadPyroFile (newLocalFileName, pyroFile)


def downloadPyroFile (clientFileName, pyroFile, size = 1024):
    """
    Allows to upload given local file to a remote location (represented by Pyro file hanfdle).

    :param str clientFileName: path to existing local file on a client where we are
    :param PyroFile pyroFile: represenation of remote file, this file will be created
    :param int size: optional chunk size. The data are read and written in byte chunks of this size 
    """
    file = open (clientFileName, 'rb')
    data = file.read(size)
    while data:
        pyroFile.setChunk(data)
        data = file.read(size)
    file.close()
    pyroFile.close()

def downloadPyroFileOnServer (clientFileName, pyroFile, size = 1024):
    """
    See :func:'downloadPyroFile'
    """
    downloadPyroFile (clientFileName, pyroFile, size)

