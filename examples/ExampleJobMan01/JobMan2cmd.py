import conf
import socket

from mupif import PyroUtil
import logging
logger = logging.getLogger()

import Pyro4
import getopt, sys

print "JobMan2cmd: ", sys.argv[1:]

def usage():
    print "Usage: JobMan2cmd -p portnumber -j jobid -n natport"

try:
    opts, args = getopt.getopt(sys.argv[1:], "p:j:n:", ['port=','job=','natport='])
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
    elif o in ("-n", "--natport"):
        natPort = int(a)
    else:
        assert False, "unhandled option"

if natPort == -1:
    natPort = daemonPort


#locate nameserver
ns = PyroUtil.connectNameServer(conf.nshost, conf.nsport, "mmp-secret-key")

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
nathost='localhost'
try:
    daemon = Pyro4.Daemon(host=conf.daemonHost, port=daemonPort, nathost=nathost, natport=natPort)
except Exception as e:
    logger.debug('Daemon can not be started: host:%s, port:%d, nathost:%s, natport:%d' % (conf.daemonHost, daemonPort, nathost, natPort))
    logger.exception(e)


#Initialize application
#app = DemoApplication.DemoApplication()
app = conf.appClass()
app.registerPyro(daemon, ns)


#register agent
uri = daemon.register(app)
ns.register(jobID, uri)

#
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10000))
s.sendall(uri.asString())
s.close()

print 
print "done"

daemon.requestLoop()



