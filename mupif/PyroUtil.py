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
import Pyro4
import socket
import subprocess
import time 
#debug flag
debug = 0

logging.basicConfig(filename='mupif.pyro.log',filemode='w',level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x
Pyro4.config.SERIALIZERS_ACCEPTED={'pickle'}




def connectNameServer(nshost, nsport):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect((nshost, nsport))
        s.shutdown(2)
        if debug: 
            print ("Connected to nameserver's LISTENING port on " + nshost + ":" + str(nsport))
    except Exception as e:
        print ("Cannot connect to nameserver's LISTENING port on " + nshost + ":" + str(nsport) + ". Is a Pyro4 nameserver running there? Does a firewall block INPUT or OUTPUT on the port?")
        logging.exception(e)
        exit(0)

    #locate nameserver
    ns     = Pyro4.locateNS(host=nshost, port=nsport)
    return ns


def connectApp(ns, name):
    uri = ns.lookup(name)
    app2 = Pyro4.Proxy(uri)
    try:
        sig = app2.getApplicationSignature()
        if debug:
            print ("Connected to "+sig)
    except Exception as e:
        print ("Cannot connect to application " + name + ". Is the server running?" )
        logging.exception(e)
        exit(0)
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
    
    #register agent
    uri    = daemon.register(app)
    ns.register(nsname, uri)
    print (nsname, uri)
    daemon.requestLoop()

        

def sshTunnel(remoteHost, userName, localPort, remotePort):
    if debug:
        print("sshTunnel command: %s" % ('ssh '+'-L '+ '{}:{}:{} '.format(localPort, remoteHost, remotePort)+ '{}@{} '.format(userName, remoteHost)+'-N'))
    tunnel = subprocess.Popen(['ssh','-L', '{}:{}:{}'.format(localPort, remoteHost, remotePort), '{}@{}'.format(userName, remoteHost),'-N'])
    time.sleep(0.5)
    return tunnel
