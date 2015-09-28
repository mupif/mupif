from __future__ import print_function
from builtins import str
import sys

import socket
import getopt, sys
import logging
import importlib



def usage():
    print("Usage: JobMan2cmd -p portnumber -j jobid -n natport -d workdir -f inputfile")

def main():
    #Results are printed through a logger only - communication with this subprocess is peculiar
    logger = logging.getLogger()
    logger.info ("JobMan2cmd: " + str(sys.argv[1:]))

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:j:n:d:f:s:i:c:", ['port=','job=','natport='])
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
        elif o in ("-f", "--file"):
            inputfile = a
        elif o in ("-s", "--socket"):
            jobManCommPort = int(a)
        elif o in ("-i", "--include"):
            moduleDir = a
        elif o in ("-c", "--config"):
            configName = a
        else:
            assert False, "unhandled option"


    if daemonPort == None or jobID == None:
        logger.error('missing options -p and -j')
        usage()
        sys.exit(2)

    if natPort == -1:
        natPort = daemonPort

    if configName:
        if moduleDir:
            sys.path.append(moduleDir)
        conf = importlib.import_module(configName)
        mupif= importlib.import_module('mupif')
    else:
        logger.error('missing options -c specifying server config file')


    #Results are printed through a logger only - communication with this subprocess is peculiar
    logger = logging.getLogger()

    #locate nameserver
    ns = mupif.PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

    #Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
    daemon = mupif.PyroUtil.runDaemon(host=conf.daemonHost, port=daemonPort, nathost=conf.nathost, natport=natPort)

    #Initialize application
    #app = DemoApplication.DemoApplication()
    app = conf.applicationClass("input.in",workDir)

    #register agent
    uri = daemon.register(app)
    ns.register(jobID, uri)
    app.registerPyro(daemon, ns, uri)
    #app.setWorkingDirectory(workDir)
    logger.info('JobMan2cmd: ns registered %s with uri %s', jobID, uri)
    logger.info('JobMan2cmd: setting workdir as %s', workDir)
    logger.info('Signature is %s' % app.getApplicationSignature() )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', jobManCommPort))
    s.sendall(uri.asString())
    s.close()

    daemon.requestLoop()
    
if __name__ == '__main__':
    main()
