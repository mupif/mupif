import serverConfig as conf
import socket
import getopt, sys
import logging
import os

from mupif import *
#Results are printed through a logger only - communication with this subprocess is peculiar
logger = logging.getLogger()

def usage():
    print "Usage: JobMan2cmd -p portnumber -j jobid -n natport -d workdir"

print "JobMan2cmd: ", sys.argv[1:]

try:
    opts, args = getopt.getopt(sys.argv[1:], "p:j:n:d:", ['port=','job=','natport='])
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
    elif o in ("-d", "--workdir"):
        workDir = a
    else:
        assert False, "unhandled option"

if daemonPort == None or jobID == None:
    logger.error('missing options -p and -j')
    usage()
    sys.exit(2)

if natPort == -1:
    natPort = daemonPort


#locate nameserver
ns = PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

#Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
daemon = PyroUtil.runDaemon(host=conf.deamonHost, port=daemonPort, nathost=conf.nathost, natport=natPort)

#Initialize application
#app = DemoApplication.DemoApplication()
app = conf.applicationClass()

#register agent
uri = daemon.register(app)
ns.register(jobID, uri)
app.registerPyro(daemon, ns, uri)

#create working directory if not present
jobDir = workDir+'/'+jobID
logger.info("Checking working directory:"+jobDir)
if not os.path.exists(jobDir):
    logger.info("Creating job working directory:"+jobDir)
    os.makedirs(jobDir)
app.setWorkingDirectory(jobDir)

logger.info('Signature is %s' % app.getApplicationSignature() )

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 10000))
s.sendall(uri.asString())
s.close()

daemon.requestLoop()
