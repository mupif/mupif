#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2014 Borek Patzak
#
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301  USA
import os
import re
import Pyro5
import socket
import getpass
import subprocess
import threading
import logging
import time
import json
import atexit
import signal
import collections
import random
import urllib.parse
import os.path
import deprecated
from . import model
from . import modelserverbase
from . import util
from . import apierror
from .pyrofile import PyroFile
import pydantic
log = logging.getLogger()

Pyro5.config.SERIALIZER = "serpent"
# Pyro4.config.THREADPOOL_SIZE=100
Pyro5.config.SERVERTYPE = "multiplex"

Pyro5.config.COMMTIMEOUT = 60

import importlib.resources


from dataclasses import dataclass
from typing import Optional


# pyro5 nameserver metadata
class _NS_METADATA:
    jobmanager = "type:jobmanager"
    appserver = "type:appserver"
    network = "network:"  # plus JSON


def runNameserverBg(nshost=None, nsport=None):
    import threading
    threading.current_thread().name = 'mupif-nameserver'
    import Pyro5.configure
    Pyro5.configure.SERIALIZER = 'serpent'
    Pyro5.configure.PYRO_SERVERTYPE = 'multiplex'
    Pyro5.configure.PYRO_SSL = 0
    log.debug(Pyro5.configure.global_config.dump())
    nshost, nsport, nssrc = locateNameserver(nshost, nsport, server=True)
    import Pyro5.nameserver
    log.info(f"Starting nameserver on {nshost}:{nsport} (via {nssrc})")
    nsUri, nsDaemon, nsBroadcast = Pyro5.nameserver.start_ns(nshost, nsport)

    def _nsBg():
        try:
            nsDaemon.requestLoop()
        finally:
            nsDaemon.close()
            if nsBroadcast is not None:
                nsBroadcast.close()
    thread = threading.Thread(target=_nsBg, daemon=True).start()
    h, p = nsDaemon.locationStr.rsplit(':', 1)  # handles both ipv4 and ipv6
    log.info(f'Nameserver up at {h}:{p}')
    NameserverBg = collections.namedtuple('NameserverBg', ['host', 'port', 'thread'])
    return NameserverBg(host=h, port=p, thread=thread)


def locateNameserver(nshost=None, nsport=0, server=False, return_src=False):
    def fromFile(f):
        s = urllib.parse.urlsplit('//'+open(f, 'r').readlines()[0].strip())
        log.info(f'Using {f} → nameserver {s.hostname}:{s.port}')
        return s.hostname, s.port, f'file://{os.path.abspath(f)}'
    # 1. set from arguments passed

    # for the server, 0.0.0.0 binds all local interfaces
    # for the client, 0.0.0.0 is meaningless
    # if nshost=='0.0.0.0' or nshost=='::':
    #    if server: return nshost,nsport
    #    else: return None,nsport
    if nshost is not None:
        log.info(f'Using nameserver arguments {nshost}:{nsport}')
        return nshost, nsport, 'explicit'

    # 2. set from MUPIF_NS env var
    if nshp := os.environ.get('MUPIF_NS', None):
        s = urllib.parse.urlsplit('//'+nshp)
        log.info(f'Using MUPIF_NS environment variable → nameserver {s.hostname}:{s.port}')
        return s.hostname, s.port, 'env:MUPIF_NS'
    # 3. from MUPIF_NS in cwd
    if os.path.exists(nshp := os.getcwd()+'/MUPIF_NS'):
        return fromFile(nshp)
    # 4. set from MUPIF_NS *file* in mupif module directory
    import mupif
    if os.path.exists(nshp := os.path.dirname(mupif.__file__)+'/MUPIF_NS'):
        return fromFile(nshp)
    # 4. set from XDG user-config file (~/.config/MUPIF_NS on linux)
    try:
        import appdirs
        if os.path.exists(nshp := (appdirs.user_config_dir()+'/MUPIF_NS')):
            return fromFile(nshp)
    except ImportError:
        log.warning('Module appdirs not installed, not using user-level MUPIF_NS config file.')
    if server:
        log.warning('Falling back to 127.0.0.1:9090 for nameserver (server).')
        return '127.0.0.1', 9090, 'fallback-server'
    else:
        log.warning('Falling back to 0.0.0.0:0 for nameserver (client).')
        return None, 0, 'fallback-client'


@deprecated.deprecated('renamed to connectNameserver')
def connectNameServer(*args, **kw): return connectNameserver(*args, **kw)


@pydantic.validate_arguments
def connectNameserver(nshost: Optional[str] = None, nsport: int = 0, timeOut: float = 3.0) -> Pyro5.client.Proxy:
    """
    Connects to a NameServer.

    :param str nshost: IP address of nameServer
    :param int nsport: Nameserver port.
    :param float timeOut: Waiting time for response in seconds
    :return: NameServer
    :rtype: Pyro5.naming.Nameserver
    :raises Exception: When can not connect to a LISTENING port of nameserver
    """

    if nshost == '0.0.0.0' or nshost == '::':
        nshost = None

    nshost, nsport, nssrc = locateNameserver(nshost, nsport)

    if nshost is not None and nsport != 0:
        try:
            conn = socket.create_connection((nshost, nsport), timeout=timeOut)
            log.debug(f'Connection to {nshost}:{nsport} is possible.')
            conn.close()
        except Exception:
            log.exception(f'Socket pre-check failed: can not connect to a LISTENING port of nameserver on {nshost}:{nsport}. Does a firewall block INPUT or OUTPUT on the port?')
            raise

    # locate nameserver
    try:
        ns = Pyro5.api.locate_ns(host=nshost, port=int(nsport))
        log.debug(f"Connected to NameServer on {nshost}:{nsport}. Pyro5 version on your localhost is {Pyro5.__version__}.")
    except Exception:
        log.exception(f"Unable to locate nameserver at {nshost}:{nsport}. Is the NameServer running? Runs the NameServer on the same Pyro version as this version {Pyro5.__version__}? Exiting.")
        raise
    return ns


# global variable holding daemon objects, keyed by hostname (local IP address)
_daemons = {}


def getDaemon(proxy: Pyro5.api.Proxy = None, exclusive=False) -> Pyro5.api.Daemon:
    """
    Returns a daemon which is bound to this process lifetime (running in a separate thread, which will terminate automatically when the main process exits) and which can talk to given *proxy* object. The *proxy* object is used to find out the local network address the daemon will listen on; the remote object must connectible when this function is called. The daemons are cached, based on the local network address, i.e. the first call for the network address will construct the daemon and subsequent calls will only return the already running daemon.

    Passing *proxy=None* will return the (possibly cached) daemon listening on the IPv4 loopback interface.

    Do *not* call ``shutdown`` on the daemon returned as this would break the caching involved.
    """
    if proxy is not None:
        proxy._pyroBind()
        host = proxy._pyroConnection.sock.getsockname()[0]
    else:
        host = '127.0.0.1'
    global _daemons
    if not exclusive and ((d := _daemons.get(host, None)) is not None):
        log.debug(f're-using existing daemon for {host}: {d.locationStr} [pid={os.getpid()}]')
        return d
    dNew = _daemons[host] = Pyro5.api.Daemon(host=host)
    th = threading.Thread(target=dNew.requestLoop, daemon=(not exclusive))
    th.start()
    log.debug(f'started new {"NON-" if exclusive else ""}exclusive daemon for {host}: {dNew.locationStr} [pid={os.getpid()}]')
    return dNew


def getNSmetadata(ns, name):
    """
    Returns name server metadata for given entry identified by name
    :return entry metadata 
    :rtype: list of strings
    """
    (uri, mdata) = ns.lookup(name, return_metadata=True)
    return mdata


def getNSConnectionInfo(ns, name):
    """
    Returns component connection information stored in name server 
    :return (host, port, nathost, natport) tuple
    :rtype: tuple
    """
    mdata = getNSmetadata(ns, name)
    for md in mdata:
        if not md.startswith(_NS_METADATA.network):
            continue
        d = json.loads(md[len(_NS_METADATA.network):])
        return d.get('host', None), d.get('port', None)
    return None, None


def _connectApp(ns, name, connectionTestTimeOut=10.):
    """
    Connects to a remote application.

    :param Pyro5.naming.Nameserver ns: Instance of a nameServer
    :param str name: Name of the application to be connected to
    :param connectionTestTimeOut timeout for connection test
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application or Timeout passes
    """
    try:
        uri = ns.lookup(name)
        log.debug(f"Application {name}, found URI {uri} on {getNSConnectionInfo(ns,name)} from a nameServer {ns._pyroUri}")
        app2 = Pyro5.api.Proxy(uri)
    except Exception as e:
        log.error(f"Cannot find registered server {name} on {ns}")
        raise

    try:
        log.info(f"Connecting to application {name} with {app2._pyroUri}")
        # By default, Pyro waits an indefinite amount of time for the call to return. 
        # When testing connection to an remote object via _connectApp, the object getSignature method is called.
        # The connection timeout is set for this call. after this, the timeout is reset to default.
        # When timeout is passed, Pyro4.errors.CommunicationError is thrown.
        # This is essential to detect the case when, for example, object has been registered at namesever, 
        # but is not operational at the moment.
        app2._pyroTimeout = connectionTestTimeOut
        sig = app2.getApplicationSignature()
        app2._pyroTimeout = None
        log.debug("Connected to " + sig + " with the application " + name)
    except Pyro5.core.errors.CommunicationError as e:
        log.exception("Communication error (network config?).")
        print("|".join(Pyro5.errors.get_pyro_traceback()))
        raise
    except Exception as e:
        log.exception(f"Cannot connect to application {name}. Is the server running?")
        raise

    return app2


def connectApp(ns, name, connectionTestTimeOut=10.):
    return _connectApp(ns, name, connectionTestTimeOut)


def _connectAppWithMetadata(ns, requiredMData, optionalMData=[], connectionTestTimeOut=10.):
    """
    Connects to a remote service with required (and optional) metadata.

    :param Pyro5.naming.Nameserver ns: Instance of a nameServer
    :param set[str] requiredMData: list of compulsory, required metadata the service should match
    :param set[str] optionalMData: list of optional metadata of the service 
    :param connectionTestTimeOut timeout for connection test
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application or Timeout passes
    """
    try:
        candidates = ns.yplookup(meta_all=requiredMData)
        if not candidates:
            raise Exception('_connectAppWithMetadata: NS yplookup failed')
        # now to select optimal candidate
        # if optionalMData are empty select random one
        candidateScores = {}
        print("Candidates:", candidates)
        # assign each candidate a score 
        for key, value in candidates.items():
            name = key
            if (not optionalMData):
                candidateScores[name]=1 # all candidates will have the same score if no optional metedata 
            else:
                # value[0] URI, value[1] metadata
                # select the optimal one as the one matching max number of optionalMData entries
                score = len(optionalMData.intersection(value[1]))
                candidateScores[name]=score
        
        # now sort candidates (mekes sense onbly if optional metadata exist)
        if (not optionalMData):
            orderedCandidates = candidates
        else:
            orderedCandidates = collections.OrderedDict(sorted(candidates.items(), key=lambda item: item[1], reverse=True))
        
        #ok now go over orderedCandidates and try to connect 
        for key, val in orderedCandidates.items():
            name = key
            uri=val[0]
            app = Pyro5.api.Proxy(uri)
            log.info(f"Trying to Connect to application {name} with {uri}")
            try:
                app._pyroTimeout = connectionTestTimeOut
                sig = app.getApplicationSignature()
                app._pyroTimeout = None
                log.info("Connected to " + sig + " with the application " + name)
                return app
            except Exception as e:
                log.exception(f"Cannot connect to application {name}. Is the server running?")
                continue
        # we ended here withou succesfull connection
        raise Exception("PyroUtil::Cannot connect to any suitable candidate")
    
    except Exception as e:
        raise

def connectAppWithMetadata(ns, requiredMData, optionalMData=[], connectionTestTimeOut=10.):
    return _connectAppWithMetadata(ns, requiredMData, optionalMData, connectionTestTimeOut)


def getNSAppName(jobname, appname):
    """
    Get application name.

    :param str jobname: Arbitrary string concatenated in the outut
    :param str appname: Arbitrary string concatenated in the outut
    :return: String of concatenated arguments
    :rtype: str
    """
    return 'Mupif'+'.'+jobname+'.'+appname


def runServer(*, appName, app, ns: Optional[Pyro5.api.Proxy]=None, daemon=None, metadata=None):
    """
    Runs a simple application server

    :param ns: nameserver Proxy
    :param str appName: Name of registered application
    :param instance app: Application instance
    :param daemon: Reference to already running daemon, if available. Optional parameter.
    :param metadata: set of strings that will be the metadata tags associated with the object registration. See pyroutil.py for valid tags. The metadata string "network:[JSON dictionary with host, port, nathost, natport]" will be automatically generated.

    :raises Exception: if can not run Pyro5 daemon
    :returns: URI
    """
    if ns is None: ns = connectNameserver()

    exclusiveDaemon = False
    if not daemon:
        # in server, daemon thread should keep the process alive
        daemon = getDaemon(proxy=ns, exclusive=True)
        # we can assume new daemon thread may be renamed to the app
        threading.current_thread().name = appName
        exclusiveDaemon = True
    # Check if application name already exists on a nameServer
    try:
        (uri, mdata) = ns.lookup(appName, return_metadata=True)
    except Pyro5.core.errors.NamingError:
        pass
    else:
        log.warning(f'Application name {appName} is already registered on name server, overwriting.')
    
    uri = daemon.register(app)
    try:
        # the same interface shared by both Model and JobManager

        # TODO: exclusiveDaemon semantics is unclear now; getDaemon can be cached
        # TODO: thus the server should never delete its own daemon?
        # TODO: we should have a way for daemon to stop when the last object deregisters...
        app.registerPyro(daemon=daemon, ns=ns, uri=uri, appName=appName, exclusiveDaemon=exclusiveDaemon)
    except Exception:
        log.exception(f'Can not register app with daemon {daemon.locationStr} on nameServer')
        raise

    ns.register(appName, uri, metadata=metadata)

    log.debug(f'Running {appName} at {uri} (nameserver: {ns._pyroUri})')

    def _remove_from_ns(sig=None, stack=None):
        log.warning(f'removing {appName} from {ns._pyroUri} (signal {sig})')
        ns._pyroClaimOwnership()
        ns.remove(appName)
        log.warning('done')
        # important: when handling a signal, reset the handler and re-emit it
        # otherwise e.g. TERM would not cause the process to terminate
        if sig is not None:
            signal.signal(sig, signal.SIG_DFL)
            log.warning(f'Re-emiting signal {sig}')
            os.kill(os.getpid(), sig)
            # os._exit(0)
    atexit.register(_remove_from_ns)  # regular process exit
    signal.signal(signal.SIGTERM, _remove_from_ns)  # terminate by signal
    return uri


def runAppServer(*, appName, app, ns):
    """
    Runs a simple application server

    :param Pyro5.api.Proxy ns: nameserver proxy
    :param str appName: Name of registered application
    :param instance app: Application instance
    :param int port: [deprecated] Port number on the server where daemon will listen (internal port number)
    :param str server: [deprecated] Host name of the server (internal host name)
    :param str nshost: [deprecated] Hostname of the computer running nameserver
    :param int nsport: [deprecated] Nameserver port

    :raises Exception: if can not run Pyro5 daemon
    """

    return runServer(
        ns=ns,
        appName=appName,
        app=app,
        metadata={_NS_METADATA.appserver}
    )




@deprecated.deprecated(reason='Use runModelServer instead')
def runJobManagerServer(*args,**kw):
    return runModelServer(*args,**kw)

def runModelServer(*, ns, jobman):
    """
    Registers and runs given jobManager server

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param jobman: Jobmanager
    """
    modelMD=jobman.getModelMetadata()
    #print(modelMD)
    estRunTime=modelMD['Solver']['Estim_comp_time_s']
    Runtime=""
    if (estRunTime < 60):
        Runtime = "Runtime_seconds"
    elif (estRunTime< 60*60):
        Runtime = "Runtime_minutes"
    elif (estRunTime<60*60*24):
        Runtime = "Runtime_hours"
    else:
        Runtime = "Runtime_days"

    # use jobnman.getNSName() as nameserver registration name, which is constructed from modelServer base name and is unique
    # inject modelServer base name into metadata as well as selected model characteristics, so later modelServer with given metadata can be looked up.
    return runServer(
        ns=ns,
        appName=jobman.getNSName(),
        app=jobman,
        metadata={_NS_METADATA.jobmanager, jobman.getName(), "Accuracy_%s"%(modelMD['Solver']['Accuracy'],), "Robustness_%s"%(modelMD['Solver']['Robustness'],), Runtime}
    )


def getIPfromUri(uri):
    """
    Returns IP address of the server hosting given URI, e.g. return 127.0.0.1 from string 
    PYRO:obj_b178eed8e1994135adf9864725f1d50f@127.0.0.1:5555
    :param str uri: URI from an object

    :return: IP address 
    :rtype: string
    """
    match = re.search(r'@([\w\.]+)\:\d+$', str(uri))
    if match:
        return match.group(1)
    else:
        log.error("getIPfromUri: uri format mismatch (%s)" % uri)
        return None


def getObjectFromURI(uri):
    """
    Returns object from given URI, e.g. returns a field
    :param str uri: URI from an object

    :return: Field, Property etc.
    :rtype: object
    """
    ret = Pyro5.api.Proxy(uri)
    return ret


def getUserInfo():
    """
    :return: tuple containing (username, hostname)
    :rtype: tuple of strings
    """
    username = getpass.getuser()
    hostname = socket.gethostname()
    return username, hostname


@deprecated.deprecated(reason='Use connectModelServer instead')
def connectJobManager(*args,**kw):
    return connectModelServer(*args,**kw)

def connectModelServer(ns, jobManName):
    """
    Connect to jobManager described by given jobManRec and create an optional ssh tunnel

    :param jobManName name under which jobmanager is registered on NS

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: jobmanager.RemoteJobManager
    :raises Exception: if creation of a tunnel failed
    """

    return modelserverbase.RemoteModelServer(_connectAppWithMetadata(ns, {jobManName}))

def connectModelServerWithMetadata(ns, metadata, optionalMetadata={}):
    """
    Connect to jobManager described by given jobManRec and create an optional ssh tunnel

    :param jobManName name under which jobmanager is registered on NS

    :return: (JobManager proxy, jobManager Tunnel)
    :rtype: jobmanager.RemoteJobManager
    :raises Exception: if creation of a tunnel failed
    """

    return modelserverbase.RemoteModelServer(_connectAppWithMetadata(ns, metadata, optionalMetadata))


@deprecated.deprecated(reason='Use allocateApplicationWithModelServer instead')
def allocateApplicationWithJobManager(*args,**kw):
    return allocateApplicationWithModelServer(*args,**kw)

def allocateApplicationWithModelServer(*, ns, jobMan, remoteLogUri):
    """
    Request new application instance to be spawned by  given jobManager.
    
    :param Pyro5.naming.Nameserver ns: running name server
    :param jobManager jobMan: jobmanager to use
    :param remoteLogUri: remote log URI

    :returns: Application instance
    :rtype: model.RemoteModel
    :raises Exception: if allocation of job fails
    """

    log.debug('Trying to connect to JobManager')
    try:
        (username, hostname) = getUserInfo()
        # signature of allocateJob changed, support both versions
        try:
            status, jobid, jobport = jobMan.allocateJob(user=username+"@"+hostname, remoteLogUri=remoteLogUri)
        except TypeError:
            status, jobid, jobport = jobMan.allocateJob(user=username+"@"+hostname)
            log.warning('ModelServerBase.allocateJob failed with remoteLogUri, remote logging disabled.')
        log.info(f'Allocated job, returned record from modelServer: {status},{jobid},{jobport}')
    except Exception:
        log.exception("ModelServerBase allocateJob() failed")
        print("| ".join(Pyro5.errors.get_pyro_traceback()))
        raise
    return model.RemoteModel(_connectApp(ns, jobid), jobMan=jobMan, jobID=jobid)


def allocateNextApplication(*, ns, jobMan, remoteLogUri):
    """
    Request a new application instance to be spawned by given jobManager
    
    :param Pyro5.naming.Nameserver ns: running name server
    :param jobMan: jobmanager to use
    :param remoteLogUri: remote log URI
    
    :return: Application instance
    :rtype: model.RemoteModel
    :raises Exception: if allocation of job fails
    """
    return allocateApplicationWithModelServer(ns=ns, jobMan=jobMan, remoteLogUri=remoteLogUri)
