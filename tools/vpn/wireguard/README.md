# Running

Just run `make`, it should:

* (re)build the base Docker container with mupif, if needed`
* create 1 central node with pyro nameserver
* create 3 client nodes, each being in a different LAN (created by docker-compose) with the central node
* create wireguard VPN (via wg-quick and config files in /etc/wireguard) on the top of those network in the 192.168.132.x range (central node .1, clients .2, .3, .4)
* run example 7 on 3 clients (thermal, mechanical server and the workflow), communicating through the VPN, using nameserver on the central node (the NS does *not* have to be on the central node, however)
* all this runs with no configuration of the servers (local-noconf mode), relying on discovery of the NS and pulling information about other components from the NS
* the entire docker-compose will exit when the workflow finishes

# Wireguard config

The config was generated at https://www.wireguardconfig.com/, setting:

* Listen Port to 11111
* Number of Clients: 3
* CIDR: 192.162.132.0/24
* Client allowed IPs: same
* Endpoint: central:11111 [central is resolved by internal DNS of docker-compose]
* Post-Up, Post-Down: commented out for the setup where server is not behind NAT
* Use Pre-Shared Keys
