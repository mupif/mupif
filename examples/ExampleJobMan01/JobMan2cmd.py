import conf
import socket

import logging
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger()

from mupif import PyroUtil
import Pyro4
import getopt, sys

print "Hello: ", sys.argv[1:]

try:
    opts, args = getopt.getopt(sys.argv[1:], "p:j:")
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-p", "--port"):
        daemonPort = int(a)
    elif o in ("-j", "--job"):
        jobID = a
    else:
        assert False, "unhandled option"

#locate nameserver
ns = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = Pyro4.Daemon(host=conf.daemonHost, port=daemonPort) #, nathost="localhost", natport=6666)

#Initialize application
#app = DemoApplication.DemoApplication()
app = conf.appClass()
app.registerPyro(daemon, ns)


#register agent
uri    = daemon.register(app)
ns.register(jobID, uri)

#
HOST = 'daring.cwi.nl'    # The remote host
PORT = 50007              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10000))
s.sendall(uri.asString())
s.close()

print 
print "done"

# run request loop
daemon.requestLoop()



def usage():
    print "Usage: JobMan2cmd -p portnumber -j jobid"
