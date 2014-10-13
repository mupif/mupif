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

import sshtunnel

#debug flag
debug = 0


logging.basicConfig(filename='mupif.pyro.log',filemode='w',level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

Pyro4.config.SERIALIZER="pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION=2 #to work with python 2.x and 3.x


class SSHTunnel:
    def __init__(self, host, port, rhost, rport, userName, userPsswd, pkey=None):
        self.host=host
        self.port=port
        self.rhost=rhost
        self.rport=rport
        self.uname=userName
        self.pwd=userPsswd
        self.pkey=pkey
        
    def start(self):
        self.server = sshtunnel.SSHTunnelForwarder(
            ssh_address=(self.host, self.port),
            ssh_host_key=None,
            ssh_username=self.uname,
            ssh_password=self.pwd,
            ssh_private_key=self.pkey,
            remote_bind_address=(self.rhost, self.rport))
        server.start()
    def stop(self):
        self.server.stop()

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
    uri = ns.lookup("Mupif.application2")
    app2 = Pyro4.Proxy(uri)
    try:
        sig = app2.getApplicationSignature()
    except Exception as e:
        print ("Cannot connect to application" + name + ". Is the server running?" )
        logging.exception(e)
        exit(0)
    return app2
        
