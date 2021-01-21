from builtins import str
import sys
sys.path.extend(['..','../..', '../../..'])

import socket
import getopt
import sys
import logging
import importlib


def usage(log):
    log.info("Usage: JobMan2cmd -p portnumber -j jobid -n natport -d workdir -f inputfile -s socket -i moduleDir -c ServerConfigFile -m configMode --override-nsport nsport")


def main():
    from mupif import util
    log = util.setupLogger(fileName='JobMan2cmd.log', level=logging.DEBUG)
    log.info("JobMan2cmd: " + str(sys.argv[1:]))


    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:j:n:d:f:s:i:c:m:", ['port=', 'job=', 'natport=', 'override-nsport='])
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage(log)
        sys.exit(2)

    daemonPort = None
    jobID = None
    natPort = None
    configName = None
    moduleDir = None
    configMode = 0
    workDir = ''
    jobManCommPort = 0  # TODO check if this default value is OK
    overrideNsPort=0

    for o, a in opts:
        if o in ("-p", "--port"):
            daemonPort = a
        elif o in ("-j", "--job"):
            jobID = a
        elif o in ("-n", "--natport"):
            natPort = a
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
        elif o in ("-m", "--mode"):
            configMode = int(a)
        elif o in ('--override-nsport'):
            overrideNsPort=int(a)
        else:
            log.error("unhandled option")

    if daemonPort is None or jobID is None:
        log.error('missing at least options -p and -j')
        usage(log)
        sys.exit(2)

    if configName:
        if moduleDir:
            sys.path.append(moduleDir)
        moduleImport = importlib.import_module(configName)
        print(moduleImport)
        conf = moduleImport.serverConfig(configMode)
        if overrideNsPort>0:
            log.info('Overriding config-specified nameserver port %d with --override-nsport=%d'%(conf.nsport,overrideNsPort))
            conf.nsport=overrideNsPort
        # conf = moduleImport.variables(configMode)
        # import pyroutil module from mupif
        # mupif = importlib.import_module('mupif')
        pyroutil = importlib.import_module('mupif.pyroutil')

        if natPort == 'None' or natPort is None:
            natPort = None
        elif conf.serverNathost is None:
            conf.serverNathost = conf.server

        # locate nameserver
        ns = pyroutil.connectNameServer(nshost=conf.nshost, nsport=conf.nsport)

        # Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
        # if conf.serverNathost==None:
        #     conf.serverNathost = conf.server

        daemon = pyroutil.runDaemon(host=conf.server, port=int(daemonPort), nathost=conf.serverNathost, natport=natPort)
        log.info(f'Running daemon {conf.server}%s:{daemonPort} (NAT {conf.serverNathost}:{natPort})')
        # Initialize application
        # app = DemoApplication.DemoApplication()
        log.info(
            'Initializing application with initial file %s and workdir %s' % (conf.applicationInitialFile, workDir))
        app = conf.applicationClass()
        try:
            # app.initialize(file=conf.applicationInitialFile, workdir=workDir)

            # register agent
            uri = daemon.register(app)
            metadata = {pyroutil.NS_METADATA_appserver,
                        '%s:%s' % (pyroutil.NS_METADATA_host, conf.server),
                        '%s:%s' % (pyroutil.NS_METADATA_port, daemonPort),
                        '%s:%s' % (pyroutil.NS_METADATA_nathost, conf.serverNathost),
                        '%s:%s' % (pyroutil.NS_METADATA_natport, natPort)}
            ns.register(jobID, uri, metadata=metadata)
            app.registerPyro(daemon, ns, uri, jobID)
            # app.setWorkingDirectory(workDir)
            log.info('JobMan2cmd: ns registered %s with uri %s', jobID, uri)
            # log.info('JobMan2cmd: setting workdir as %s', workDir)
            log.info('Signature is %s' % app.getApplicationSignature())

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', jobManCommPort))
            # needs something w/ buffer interface, which is bytes (and not str)
            s.sendall(bytes(str(uri), 'utf-8'))
            s.close()
            daemon.requestLoop()

        except Exception as e:
            log.exception(e)
            app.terminate()

    else:
        log.error('missing options -c specifying server config file')
        exit(0)


if __name__ == '__main__':
    main()
