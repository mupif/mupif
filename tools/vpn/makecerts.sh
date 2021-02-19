#!/bin/bash
#
# This VPN configuration was roughly following https://www.digitalocean.com/community/tutorials/how-to-set-up-an-openvpn-server-on-ubuntu-16-04 .
#
# For generalities about VPN, see the MuPIF User manual. 
#
# This script will work on debian/ubuntu machines, and needs the easy-rsa package to be installed.
#
# Generated configuration files need to be hand-adapted before use.
#

# name of clients for which client configuration files will be generated
CLIENTS="client1 client2 client3"

make-cadir mupif-ca # from easy-rsa package
pushd mupif-ca
	source vars
	./clean-all
	#
	# SERVER KEYS
	#
	./build-ca # confirm everything
	./build-key-server server # confirm everything, empty challenge password, sign & commit the cert (y and y) at the endd
	./build-dh
	openvpn --genkey --secret keys/ta.key
	#
	# CLIENT KEYS (repeat for all clients)
	#
	for CLIENT in $CLIENTS; do
		./build-key $CLIENT # confirm everything, empty password, y & y for sign & commi
	done
popd

#
# OpenVPN SERVER CONFIG
#
mkdir -p config/server

cp mupif-ca/keys/{ca.crt,ca.key,server.crt,server.key,ta.key,dh2048.pem} config/server
gunzip -c /usr/share/doc/openvpn/examples/sample-config-files/server.conf.gz | sudo tee config/server/server.conf
# make some modifications here
# The configuration will make the server listen at all interfaces, port 1194; real scenarios expose the server on an external interface and set firewall rules accordingly. It will take 192.18.0.1/16 as its own address and use the rest of this network for clients (this network range is assigned to inter-nectwork communications, so OK to use it here, purely for testing).
for CLIENT in $CLIENTS; do
	mkdir -p config/$CLIENT
	chmod 700 config/$CLIENT
	cp /usr/share/doc/openvpn/examples/sample-config-files/client.conf config/$CLIENT/base.conf
	# modify as needed
	cp mupif-ca/keys/{ca.crt,ta.key,$CLIENT.crt,$CLIENT.key} config/$CLIENT/
	# config file may refer to the private directory for certificates, but they can also be put inline using XML-like syntax as explained in e.g.  http://www.featvpn.com/demo-file-xml-based-config-file-possible; this way a standalone .ovpn config file is produced, which can be used at clients with GUI tools for connecting to the VPN
	cat config/$CLIENT/base.conf <(printf '<ca>\n') config/$CLIENT/ca.crt <(printf '</ca>\n<cert>\n') config/$CLIENT/$CLIENT.crt <(printf '</cert>\n<key>\n') config/$CLIENT/$CLIENT.key <(printf '</key>\n<tls-auth>\n') config/$CLIENT/ta.key <(printf '</tls-auth>\n') > config/$CLIENT.ovpn
	# now transfer the client/client1.ovpn config file to the client by yourself
done

#
# SERVER start
# start the server by issuing the following command  (run as admin or under sudo)
#sudo openvpn --cd server --config config/server.conf
# and leave it running (that is the OpenVPN server which will serve clients subsequently)
# just make sure clients can reach it without interfering with firewall or somesuch
#
# CLIENT start
# use client1.ovpn and feed it into NetworkManager or whatever your OS uses. Or use command-line (run under sudo or as admin)
#sudo openvpn --cd client --config config/client1.ovpn
# both client and server should say "Initialization Sequence Completed" after successful startup (server) or connection to the server (client)
