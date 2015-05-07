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
import logging
formatLog = '%(asctime)s %(levelname)s:%(filename)s:%(lineno)d %(message)s \n'
formatTime = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename='mupif.log',filemode='w',format=formatLog,level=logging.DEBUG)
logger = logging.getLogger()#create a logger
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(formatLog, formatTime))
logger.addHandler(ch)

import Pyro4
import socket
import getpass
import subprocess
import time
import RemoteAppRecord

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
    :except: Can not connect to a LISTENING port of nameserver
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeOut)
        s.connect((nshost, nsport))
        s.close()
        logger.debug("Can connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport))
    except Exception as e:
        msg = "Can not connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport) + ". Does a firewall block INPUT or OUTPUT on the port? Exiting."
        logger.debug(msg)
        logger.exception(e)
        exit(1)

    #locate nameserver
    try:
        ns = Pyro4.locateNS(host=nshost, port=nsport,hmac_key=hkey)
        msg = "Connected to NameServer on %s:%s. Pyro4 version on this computer is %s" %(nshost, nsport, Pyro4.constants.VERSION)
        logger.debug(msg)
    except Exception as e:
        msg = "Can not connect to NameServer on %s:%s. Is the NameServer running? Runs the NameServer on the same Pyro version as this version %s? Do you have the correct hmac_key (password is now %s)? Exiting." %(nshost, nsport, Pyro4.constants.VERSION, hkey)
        logger.debug(msg)
        logger.exception(e)
        exit(1)
    return ns


def connectApp(ns, name):
    """
    Connects to a remote application.

    :param Pyro4.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :return: Application
    :rtype: Instance of an application
    :except: Cannot find registered server or Cannot connect to application
    """
    try:
        uri = ns.lookup(name)
        logger.debug("Found URI %s from a nameServer %s" % (uri, ns) )
    except Exception as e:
        logger.error("Cannot find registered server %s on %s" % (name, ns) )
        return None
    app2 = Pyro4.Proxy(uri)
    try:
        sig = app2.getApplicationSignature()
        logger.debug("Connected to " + sig + " with the name " + name)
    except Exception as e:
        logger.debug("Cannot connect to application " + name + ". Is the server running?")
        logger.exception(e)
        return None
        #exit(e)
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
        logger.info('Pyro4 daemon runs on %s:%d using nathost %s:%d' % (host, port, nathost, natport))
    except socket.error as e:
        logger.debug('Socket port seems to be already in use :%d' % (port))
        daemon = None
        raise e

    except Exception as e:
        logger.debug('Can not run Pyro4 daemon on %s:%d using nathost %s:%d' % (host, port, nathost, natport))
        logger.exception(e)
        daemon = None
        raise e

    return daemon

def runAppServer(server, port, nathost, natport, nshost, nsport, nsname, hkey, app):
    """
    Runs a simple application server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nathost: Hostname of the server as reported by nameserver, for secure ssh tunnel it should be set to 'localhost' (external host name)
    :param int natport: Server NAT port as reported by nameserver (external port)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param str nsname: Nameserver name to register application
    :param str hkey: A password string
    :param instance app: Application instance

    :except: Can not run Pyro4 daemon
    """
    try:
        daemon = Pyro4.Daemon(host=server, port=port, nathost=nathost, natport=natport)
        logger.info('Pyro4 daemon runs on %s:%d using nathost %s:%d and hkey %s' % (server, port, nathost, natport, hkey))
    except Exception as e:
        logger.debug('Can not run Pyro4 daemon on %s:%d using nathost %s:%d  and hmac %s' % (server, port, nathost, natport, hkey))
        logger.exception(e)
        exit(1)
    ns = connectNameServer(nshost, nsport, hkey)
    #register agent
    uri = daemon.register(app)
    ns.register(nsname, uri)
    app.registerPyro(daemon, ns, uri)

    logger.debug('NameServer %s has registered uri %s' % (nsname, uri) )
    logger.debug('Running runAppServer: server:%s, port:%d, nathost:%s, natport:%d, nameServer:%s, nameServerPort:%d, nameServerName:%s, URI %s' % (server, port, nathost, natport, nshost, nsport,nsname,uri) )
    daemon.requestLoop()


def sshTunnel(remoteHost, userName, localPort, remotePort, sshClient='ssh', options='', sshHost=''):
    """
    Automatic creation of ssh tunnel, using putty.exe for Windows and ssh for Linux

    :param str remoteHost: IP of remote host
    :param str userName: User name
    :param int localPort: Local port
    :param int remotePort: Remote port
    :param str sshClient: Path to executable ssh client (on Windows use double backslashes 'C:\\Program Files\\Putty\putty.exe')
    :param str options: Arguments to ssh clinent, e.g. the location of private ssh keys
    :param str sshHost: Computer used for tunelling, optional. If empty, equals to remoteHost

    :return: Instance of subprocess.Popen running the tunneling command
    :rtype: subprocess.Popen
    """

    if sshHost =='':
        sshHost = remoteHost
    #use direct system command. Paramiko or sshtunnel do not work.
    #put ssh public key on a server - interaction with a keyboard for password will not work here (password goes through TTY, not stdin)
    if sshClient=='ssh':
        cmd = 'ssh -L %d:%s:%d %s@%s -N %s' % (localPort, remoteHost, remotePort, userName, sshHost, options)
        logger.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='autossh':
        cmd = 'autossh -L %d:%s:%d %s@%s -N %s' % (localPort, remoteHost, remotePort, userName, sshHost, options)
        logger.debug("Creating autossh tunnel via command: " + cmd)
    elif 'putty' in sshClient.lower():
        #need to create a public key *.ppk using puttygen. It can be created by importing Linux private key. The path to that key is given as -i option
        cmd = '%s -L %d:%s:%d %s@%s -N %s' % (sshClient, localPort, remoteHost, remotePort, userName, sshHost, options)
        logger.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='manual':
        #You need ssh server running, e.g. UNIX-sshd or WIN-freesshd
        cmd1 = 'ssh -L %d:%s:%d %s@%s' % (localPort, remoteHost, remotePort, userName, sshHost)
        cmd2 = 'putty.exe -L %d:%s:%d %s@%s %s' % (localPort, remoteHost, remotePort, userName, sshHost, options)
        logger.info("If ssh tunnel does not exist, do it manually using a command e.g. " + cmd1 + " , or " + cmd2)
        return None
    else:
        logger.error("Unknown ssh client, exiting")
        exit(0)
    try:
        tunnel = subprocess.Popen(cmd.split())
    except Exception as e:
        logger.debug("Creation of a tunnel failed. Can not execute the command: %s " % cmd)
        logger.exception(e)
        tunnel = None
    time.sleep(1.0)

    return tunnel 


def getUserInfo ():
    """
    :return: String assembled from username+"@"+hostname
    :rtype: str
    """
    username = getpass.getuser()
    hostname = socket.gethostname()
    return username+"@"+hostname

def connectJobManager (ns, jobManRec):
    """
    Connect to jobManager described by given jobManRec and create a ssh tunnel

    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see client-conf.py

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: tuple (JobManager, subprocess.Popen)
    """    

    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    #create tunnel to JobManager running on (remote) server
    try:
        tunnelJobMan = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=jobManNatport, remotePort=jobManPort, sshClient='ssh')
    except Exception as e:
        logger.debug("Creating ssh tunnel for JobManager failed")
        logger.exception(e)
        raise (e)
    else:
        # locate remote jobManager on (remote) server
        jobMan = connectApp(ns, jobManName)
        return (jobMan, tunnelJobMan)


def allocateApplicationWithJobManager (ns, jobManRec, natPort):
    """
    Connect to jobManager described by given jobManRec

    :param Pyro4.naming.Nameserver ns: running name server
    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see clientConfig.py
    :param int natPort: nat port in local computer for ssh tunnel for the application

    :return: RemoteAppRecord containing application, tunnel to application, tunnel to jobman, jobid
    :rtype: RemoteAppRecord
    :except: allocation of tunnel failed
    """    
    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    (jobMan, tunnelJobMan) = connectJobManager (ns, jobManRec)

    try:
        retRec = jobMan.allocateJob(getUserInfo(), natPort=natPort)
        logger.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception as e:
        logger.info("jobMan.allocateJob() failed")
        logger.exception(e)
        raise (e)

    #create tunnel to application's daemon running on (remote) server
    try:
        tunnelApp = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=natPort, remotePort=retRec[2], sshClient='ssh')
    except Exception as e:
        logger.info("Creating ssh tunnel for application's daemon failed")
        logger.exception(e)
        raise (e)
    else:
        logger.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    #time.sleep(1)
    # connect to (remote) application, requests remote proxy
    app = connectApp(ns, retRec[1])
    return RemoteAppRecord.RemoteAppRecord(app, tunnelApp, jobMan, tunnelJobMan, retRec[1])

def allocateNextApplication (ns, jobManRec, natPort, appRec):
    """
    Allocate next application on a running Job Manager

    :param Pyro4.naming.Nameserver ns: running name server
    :param tuple jobManRec: tuple containing (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManDNSName), see clientConfig.py
    :param int natPort: nat port in local computer for ssh tunnel for the application
    :param RemoteAppRecord appRec: existing RemoteAppRecord where a new application will be added

    :return: None
    :except: allocation or tunnel failed
    """
    (jobManPort, jobManNatport, jobManHostname, jobManUserName, jobManName) = jobManRec
    jobMan = connectApp(ns, jobManName)

    try:
        retRec = jobMan.allocateJob(getUserInfo(), natPort=natPort)
        logger.info('Allocated job, returned record from jobMan:' +  str(retRec))
    except Exception as e:
        logger.info("jobMan.allocateJob() failed")
        logger.exception(e)
        raise (e)

    #create tunnel to application's daemon running on (remote) server
    try:
        tunnelApp = sshTunnel(remoteHost=jobManHostname, userName=jobManUserName, localPort=natPort, remotePort=retRec[2], sshClient='ssh')
    except Exception as e:
        logger.info("Creating ssh tunnel for application's daemon failed")
        logger.exception(e)
        raise (e)
    else:
        logger.info("Scenario: Connecting to " + retRec[1] + " " + str(retRec[2]))

    app = connectApp(ns, retRec[1])
    appRec.appendNextApplication(app,tunnelApp,retRec[1])
    