import sys
import socket


#Results are printed through a logger only - communication with this subprocess is peculiar
import logging
import Pyro4
logging.basicConfig(filename='JobMan2cmd.log',filemode='w',level=logging.DEBUG)
logger = logging.getLogger()
logging.getLogger().addHandler(logging.StreamHandler()) #display also on screen

sys.path.append('../..')
from mupif import PyroUtil

import getopt, sys

import PingServerApplication

def usage():
    print "Usage: JobMan2cmd -p portnumber -j jobid -n natport"

print "JobMan2cmd: ", sys.argv[1:]

try:
    opts, args = getopt.getopt(sys.argv[1:], "p:j:n:", ['port=','job=','natport='])
except getopt.GetoptError as err:
    # print help information and exit:
    logger.exception(err)
    usage()
    sys.exit(2)

daemonPort = None
jobID = None

for o, a in opts:
    if o in ("-p", "--port"):
        daemonPort = int(a)
    elif o in ("-j", "--job"):
        jobID = a
    elif o in ("-n", "--natport"):
        natPort = int(a)
    else:
        assert False, "unhandled option"

if daemonPort == None or jobID == None:
    logger.error('missing options -p and -j')
    usage()
    sys.exit(2)

if natPort == -1:
    natPort = daemonPort


#locate nameserver
ns = PyroUtil.connectNameServer(nshost='147.32.130.137', nsport=9090, hkey='mmp-secret-key')

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = PyroUtil.runDaemon(host='localhost', port=44382, nathost='localhost', natport=natPort)

#Initialize application
#app = DemoApplication.DemoApplication()
app = PingServerApplication.PingServerApplication()
app.registerPyro(daemon, ns)


#register agent
uri = daemon.register(app)
ns.register(jobID, uri)

##
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10000))
s.sendall(uri.asString())
s.close()

#print 
#print "done"

daemon.requestLoop()



