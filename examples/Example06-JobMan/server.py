import serverConfig as conf
from mupif import *
import logging
logging.basicConfig(filename='server.log',filemode='w',level=logging.DEBUG)
logger = logging.getLogger('server')
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

# required firewall settings (on ubuntu):
# for computer running daemon (this script)
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44361 -j ACCEPT
# for computer running a nameserver
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 9090 -j ACCEPT


#locate nameserver
ns = PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

#Run a daemon for jobMamager on this machine
daemon = PyroUtil.runDaemon(host=conf.deamonHost, port=conf.jobManPort, nathost=conf.nathost, natport=conf.jobManNatport)
#Run job manager on a server
jobMan = JobManager.SimpleJobManager2(daemon, ns, conf.PingServerApplication, "Mupif.PingServerApplication", conf.jobManPortsForJobs, conf.jobManMaxJobs)

#set up daemon with JobManager
uri = daemon.register(jobMan)
#register JobManager to nameServer
ns.register(conf.jobManName, uri)
print ("Daemon for JobManager runs at " + str(uri))
#waits for requests
daemon.requestLoop()
