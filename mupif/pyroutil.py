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
import Pyro5.api
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
    #: the model server's preAllocate tickets work remotely (they expire, and are recognised when sent
    #: back over Pyro); clients must not call preAllocate remotely on servers without this tag
    tickets = "mupif:tickets-v2"
    #: prefix of the tag carrying the ID of the model a model server serves (its model metadata ``ID``):
    #: model servers registered under different names but serving the same model share this tag
    modelID = "ModelID:"
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
    thread = threading.Thread(target=_nsBg, daemon=True, name='mupif-nameserver').start()
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


@pydantic.validate_call
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

    All services registered with all the required tags are candidates; those carrying more of the
    optional tags are tried first (random order among equal ones), and the first one answering
    ``getApplicationSignature()`` is returned. For model servers, prefer
    :func:`connectModelServerWithMetadata`, which also considers their load.

    :param Pyro5.naming.Nameserver ns: Instance of a nameServer
    :param set[str] requiredMData: list of compulsory, required metadata the service should match
    :param set[str] optionalMData: list of optional metadata of the service
    :param connectionTestTimeOut timeout for connection test
    :return: Application
    :rtype: Instance of an application
    :raises Exception: When cannot find registered server or Cannot connect to application or Timeout passes
    """
    optional = frozenset(optionalMData or ())
    candidates = ns.yplookup(meta_all=set(requiredMData), return_metadata=True)
    if not candidates:
        raise Exception(f'_connectAppWithMetadata: no service registered with metadata {sorted(requiredMData)}')
    # more optional tags first; random among equal scores (spreads clients over equal services)
    ordered = sorted(candidates.items(), key=lambda item: (-len(optional & frozenset(item[1][1] or ())), random.random()))
    for name, (uri, _) in ordered:
        app = Pyro5.api.Proxy(uri)
        log.info(f"Trying to Connect to application {name} with {uri}")
        try:
            app._pyroTimeout = connectionTestTimeOut
            sig = app.getApplicationSignature()
            app._pyroTimeout = None
            log.info("Connected to " + sig + " with the application " + name)
            return app
        except Exception:
            log.exception(f"Cannot connect to application {name}. Is the server running?")
    raise Exception("PyroUtil::Cannot connect to any suitable candidate")

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


def removeOwnRegistration(ns, name: str, uri) -> bool:
    """
    Remove a nameserver entry, but only if it still points to the given object.

    A server removes its registration when it exits. If, meanwhile, another server registered
    under the same name (an old server overwrites a name it finds registered, see :func:`runServer`),
    removing the name unconditionally would make that other server unreachable although it is still
    running. Checking the URI first avoids this. The check and the removal are two nameserver calls,
    so a registration made exactly between them could still be removed; this is unlikely enough.

    :param ns: nameserver proxy
    :param name: registered name
    :param uri: URI of the object registered by the caller; if None (not known, e.g. the object was
                registered by other means), the name is removed unconditionally, as before
    :return: whether the entry was removed
    """
    if uri is not None:
        try:
            current = ns.lookup(name)
        except Pyro5.errors.NamingError:
            return False
        if str(current) != str(uri):
            log.warning(f'Not removing {name} from the nameserver: it is registered by another object now ({current}, ours was {uri})')
            return False
    try:
        ns.remove(name)
    except Pyro5.errors.NamingError:
        return False
    return True


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
        removeOwnRegistration(ns, appName, uri)
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

#: separates the base name of a model server from its instance id in the registered name (``CVUT.demo01~node2``);
#: chosen because it needs no escaping in job IDs (``N@<name>``), file names of job work directories and URLs
INSTANCE_SEPARATOR = '~'


def _isAlive(uri, timeout: float) -> bool:
    """Tell whether the object at *uri* answers ``getApplicationSignature()`` within *timeout* seconds."""
    try:
        proxy = Pyro5.api.Proxy(uri)
        proxy._pyroTimeout = timeout
        proxy._pyroMaxRetries = 1
        proxy.getApplicationSignature()
        return True
    except Exception:
        return False


def modelServerNSName(ns, jobman, aliveTimeout: float = 5.) -> str:
    """
    Choose the name under which a model server is registered in the nameserver.

    Several instances of one model server (same base name, :meth:`ModelServerBase.getName`) may
    run at once, e.g. on different hosts, to share the load. Each needs its own nameserver entry;
    clients find all of them by the base name, which every instance carries as a metadata tag
    (see :func:`runModelServer` and :mod:`mupif.modelplacement`). To stay compatible with clients
    that look a model server up by its exact base name (older mupif, other platforms), the name is:

    * ``<base>~<instance>`` if the server was given an instance id (``instance`` argument of the
      model server, or the environment variable ``MUPIF_MODELSERVER_INSTANCE``);
    * else ``<base>`` if that name is free, or registered by a server which does not answer any
      more (a stale entry left by a crashed server: it is overwritten, as before);
    * else ``<base>~<host>-<pid>``: another live instance holds the base name. Before, the second
      server silently replaced the first in the nameserver, and the first became unreachable.

    So a single model server keeps its old name, and the first of several instances stays reachable
    by clients that use exact names.

    :param ns: nameserver proxy
    :param jobman: the model server
    :param aliveTimeout: seconds to wait for the holder of the base name to answer
    :return: the name to register
    """
    base = jobman.getName()
    instance = getattr(jobman, 'instance', None)
    if instance:
        return f'{base}{INSTANCE_SEPARATOR}{instance}'
    try:
        uri = ns.lookup(base)
    except Pyro5.errors.NamingError:
        return base
    if not _isAlive(uri, aliveTimeout):
        log.warning(f'Model server name {base} is registered by an object which does not answer ({uri}): taking the name over')
        return base
    name = f'{base}{INSTANCE_SEPARATOR}{socket.gethostname()}-{os.getpid()}'
    log.warning(f'Model server name {base} is held by another running instance ({uri}): registering this one as {name}')
    return name


def runModelServer(*, ns, jobman):
    """
    Registers and runs given jobManager server

    The server is registered under the name chosen by :func:`modelServerNSName` (its base name, or
    an instance name if another instance holds the base name), tagged with ``type:jobmanager``, its
    base name and characteristics of its model (accuracy, robustness, run time), so that clients
    can find every instance offering a model by these tags.

    :param str server: Host name of the server (internal host name)
    :param int port: Port number on the server where daemon will listen (internal port number)
    :param str nshost: Hostname of the computer running nameserver
    :param int nsport: Nameserver port
    :param jobman: Jobmanager
    """
    # register under a name unique among the running instances (see modelServerNSName); runServer
    # passes it to jobman.registerPyro, after which jobman.getNSName() returns it
    return runServer(ns=ns, appName=modelServerNSName(ns, jobman), app=jobman, metadata=modelServerTags(jobman))


def modelServerTags(jobman) -> set[str]:
    """
    Return the nameserver metadata tags of a model server registration.

    Clients find model servers by these tags (see :mod:`mupif.modelplacement`); all instances of a
    model server carry the same tags:

    * ``type:jobmanager``;
    * the base name (:meth:`ModelServerBase.getName`), which workflows give as ``Jobmanager``;
    * ``ModelID:<ID>``, the ID from the model metadata, if set: shared by servers registered under
      different names which serve the same model;
    * ``Accuracy_<x>``, ``Robustness_<x>`` (from the model's ``Solver`` metadata) and
      ``Runtime_seconds|minutes|hours|days`` (from ``Solver.Estim_comp_time_s``), which execution
      profiles may require;
    * ``mupif:tickets-v2`` if the server's preAllocate tickets work remotely.

    :param jobman: the model server
    """
    modelMD = jobman.getModelMetadata()
    estRunTime = modelMD['Solver']['Estim_comp_time_s']
    if estRunTime < 60:
        runtime = "Runtime_seconds"
    elif estRunTime < 60*60:
        runtime = "Runtime_minutes"
    elif estRunTime < 60*60*24:
        runtime = "Runtime_hours"
    else:
        runtime = "Runtime_days"
    tags = {_NS_METADATA.jobmanager, jobman.getName(), f"Accuracy_{modelMD['Solver']['Accuracy']}", f"Robustness_{modelMD['Solver']['Robustness']}", runtime}
    if modelMD.get('ID', '') != '':
        tags.add(_NS_METADATA.modelID+str(modelMD['ID']))
    if getattr(jobman, 'remoteTickets', False):
        tags.add(_NS_METADATA.tickets)
    return tags


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

    # an exact lookup, so that callers asking for a particular server get it; to choose among all
    # instances of a model server, see connectModelServerWithMetadata and mupif.modelplacement
    return modelserverbase.RemoteModelServer(_connectApp(ns, jobManName))

def connectModelServerWithMetadata(ns, metadata, optionalMetadata=frozenset()):
    """
    Connect to the best model server registered with all tags in *metadata*.

    Candidates are ranked as for workflow models (:func:`mupif.modelplacement.rankCandidates`):
    servers with a free job slot first, then more of the *optionalMetadata* tags, then less loaded;
    the first one which answers is returned. To place the models of a workflow, the workflow uses
    :mod:`mupif.modelplacement` directly (with fallback when the allocation itself fails).

    :param metadata: tags the server must carry (e.g. its base name, ``ModelID:<id>``, ``Runtime_seconds``)
    :param optionalMetadata: tags preferring a server
    :rtype: modelserverbase.RemoteModelServer
    :raises RuntimeError: if no compatible server is registered or answers
    """
    from . import modelplacement as mpl
    required = frozenset(metadata) | {mpl.JOBMANAGER_TAG}
    optional = frozenset(optionalMetadata or ())
    res = ns.yplookup(meta_all=set(required), return_metadata=True)
    candidates = [mpl.Candidate(nsName=n, uri=str(u), tags=frozenset(t or ()), score=len(frozenset(t or ()) & optional)) for n, (u, t) in res.items()]
    loads = {c.nsName: mpl.serverLoad(c.uri) for c in candidates}
    for c in mpl.rankCandidates(candidates, loads):
        try:
            return modelserverbase.RemoteModelServer(_connectApp(ns, c.nsName))
        except Exception:
            log.exception(f'Cannot connect to model server {c.nsName}; trying the next one')
    raise RuntimeError(f'No model server registered with metadata {sorted(required)} is reachable.')


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
    except modelserverbase.ModelServerNoResourcesException as e:
        # an expected outcome (the server is busy): the caller retries elsewhere or later, no traceback
        log.warning(f'ModelServerBase allocateJob(): no free job slot ({e})')
        raise
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
