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
logging.basicConfig(filename='mupif.log',filemode='w',level=logging.DEBUG)
logger = logging.getLogger('mupif')
import Pyro4
import socket
import subprocess
import time 

Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}

#First, check that we can connect to a listening port of a name server
#Second, connect there

def connectNameServer(nshost, nsport, timeOut=3.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeOut)
        s.connect((nshost, nsport))
        s.shutdown(2)
        logger.debug("Can connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport))
    except Exception as e:
        msg = "Can not connect to a LISTENING port of nameserver on " + nshost + ":" + str(nsport) + ". Does a firewall block INPUT or OUTPUT on the port? Exiting."
        logger.debug(msg)
        logger.exception(e)
        exit(1)

    #locate nameserver
    try:
        ns = Pyro4.locateNS(host=nshost, port=nsport)
        msg = "Connected to NameServer on %s:%s. Pyro4 version on your local computer is %s" %(nshost, nsport, Pyro4.constants.VERSION)
        logger.info(msg)
    except Exception as e:
        msg = "Can not connect to NameServer on %s:%s. Is the NameServer running? Runs the NameServer on the same Pyro version as this version %s? Exiting." %(nshost, nsport, Pyro4.constants.VERSION)
        logger.debug(msg)
        logger.exception(e)
        exit(1)
    return ns


def connectApp(ns, name):
    try:
        uri = ns.lookup(name)
    except Exception as e:
        logger.error("Cannot find registered server %s on %s" % (name, ns) )
        return None
    app2 = Pyro4.Proxy(uri)
    try:
        sig = app2.getApplicationSignature()
        logger.debug("Connected to "+sig)
    except Exception as e:
        logger.debug("Cannot connect to application " + name + ". Is the server running?")
        logger.exception(e)
        return None
        #exit(e)
    return app2


def getNSAppName(jobname, appname):
    return 'Mupif'+'.'+jobname+'.'+appname

def runAppServer(server, port, nathost, natport, nshost, nsport, nsname, app):
    """
    Runs a simple application server
    ARGS:
       server(string) host name of the server
       port(int) port number on the server where daemon will listen
       nathost(string) hostname of the server as reported by nameserver 
         For secure ssh tunnel it should be set to 'localhost'
         For direct (or VPN) connections 'None'
       natport(int) server port as reported by nameserver
       ns(string) hostname of the computer running nameserver
       nsport(string) nameserver port
       nsname(string) nameserver name to register application
       app (Application) application instance
       """
    print ('runAppServer: server:%s, port:%d, nathost:%s, natport:%d, ns:%s, nsport:%d' % (server, port, nathost, natport, nshost, nsport))
    daemon = Pyro4.Daemon(host=server, port=port, nathost=nathost, natport=natport)
    ns     = connectNameServer(nshost, nsport)
    app.registerPyro (daemon, ns)
    #register agent
    uri    = daemon.register(app)
    ns.register(nsname, uri)
    print (nsname, uri)
    daemon.requestLoop()


def sshTunnel(remoteHost, userName, localPort, remotePort, sshClient='ssh', options=''):
    #use direct system command. Paramiko or sshtunnel do not work.
    #put ssh public key on a server - interaction with a keyboard for password will not work here (password goes through TTY, not stdin)
    if sshClient=='ssh':
        cmd = 'ssh -L %d:%s:%d %s@%s -N %s' % (localPort, remoteHost, remotePort, userName, remoteHost,options)
        logger.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='autossh':
        cmd = 'autossh -L %d:%s:%d %s@%s -N %s' % (localPort, remoteHost, remotePort, userName, remoteHost,options)
        logger.debug("Creating autossh tunnel via command: " + cmd)
    elif 'putty' in sshClient.lower():
        #need to create a public key *.ppk using puttygen. It can be created by importing Linux private key. The path to that key is given as -i option
        cmd = '%s -L %d:%s:%d %s@%s -N %s' % (sshClient, localPort, remoteHost, remotePort, userName, remoteHost, options)
        logger.debug("Creating ssh tunnel via command: " + cmd)
    elif sshClient=='manual':
        #You need ssh server running, e.g. UNIX-sshd or WIN-freesshd
        cmd1 = 'ssh -L %d:%s:%d %s@%s' % (localPort, remoteHost, remotePort, userName, remoteHost)
        cmd2 = 'putty.exe -L %d:%s:%d %s@%s %s' % (localPort, remoteHost, remotePort, userName, remoteHost, options)
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
