from __future__ import print_function
from builtins import str
import future.utils
import sys
sys.path.extend(['../..','../../..'])

import socket
import getopt, sys
import logging
import importlib
from mupif import Util

def usage():
    print("Usage: JobMan2cmd -p portnumber -j jobid -n natport -d workdir -f inputfile -s socket -i moduleDir -c ServerConfigFile")

def main():
    log = Util.setupLogger(fileName='JobMan2cmd.log', level=logging.DEBUG)
    
    log.info ("JobMan2cmd: " + str(sys.argv[1:]))

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:j:n:d:f:s:i:c:", ['port=','job=','natport='])
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage()
        sys.exit(2)

    daemonPort = None
    jobID = None
    natPort = None
    configName = None
    mupif = None
    moduleDir = None

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
        log.error('missing options -p and -j')
        usage()
        sys.exit(2)

    if natPort == -1:
        natPort = daemonPort

    if configName:
        if moduleDir:
            sys.path.append(moduleDir)
        conf = importlib.import_module(configName)
        # import PyroUtil module from mupif
        # mupif = importlib.import_module('mupif')
        PyroUtil = importlib.import_module('mupif.PyroUtil')
    else:
        log.error('missing options -c specifying server config file')
        exit(0)

    #Results are printed through a logger only - communication with this subprocess is peculiar
    log = logging.getLogger()

    #locate nameserver
    ns = PyroUtil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport, hkey=conf.hkey)

    #Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
    daemon = PyroUtil.runDaemon(host=conf.server, port=daemonPort, nathost=conf.serverNathost, natport=natPort)


    #Initialize application
    #app = DemoApplication.DemoApplication()
    app = conf.applicationClass(conf.applicationInitialFile, workDir)

    #register agent
    uri = daemon.register(app)
    metadata={PyroUtil.NS_METADATA_appserver,
              '%s:%s'%(PyroUtil.NS_METADATA_host, conf.server),
              '%s:%s'%(PyroUtil.NS_METADATA_port, daemonPort),
              '%s:%s'%(PyroUtil.NS_METADATA_nathost, conf.serverNathost),
              '%s:%s'%(PyroUtil.NS_METADATA_natport, natPort)}
    ns.register(jobID, uri, metadata=metadata)
    app.registerPyro(daemon, ns, uri,jobID)
    #app.setWorkingDirectory(workDir)
    log.info('JobMan2cmd: ns registered %s with uri %s', jobID, uri)
    log.info('JobMan2cmd: setting workdir as %s', workDir)
    log.info('Signature is %s' % app.getApplicationSignature() )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', jobManCommPort))
    # needs something w/ buffer interface, which is bytes (and not str)
    if future.utils.PY3: s.sendall(bytes(uri.asString(),'utf-8'))
    else: s.sendall(uri.asString())
    s.close()

    daemon.requestLoop()

if __name__ == '__main__':
    main()
