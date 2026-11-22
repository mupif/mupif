# from .pyroutil import connectNameserver
import Pyro5.api
import Pyro5.errors
import urllib.parse
import warnings
import pickle
import logging
from numpy import int16
import serpent
import time
import itertools
import concurrent.futures

from mupif.modelserverbase import JOBMAN_NO_RESOURCES
from .baredata import BareData
from .modelserverbase import ModelServerBase,ModelServerStatus
from typing import List,Dict,Any,Optional
import pydantic

log = logging.getLogger()

class NsInfo(pydantic.BaseModel):
    name: str
    uri: str
    metadata: List[str]


class ModelserverInfo(BareData):
    ns: NsInfo
    class NumJobs(BareData):
        max: int
        curr: int
        total: int
    numJobs: NumJobs
    jobs: List[ModelServerStatus.JobStatus]
    status: bool
    signature: str


def _query_job_log(remoteLogUri: str|None, logLines: int, timeout: float) -> List[str]:
    if not remoteLogUri: return []
    fmt = logging.Formatter(fmt='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')
    try:
        proxy=Pyro5.api.Proxy(remoteLogUri)
        proxy._pyroTimeout=timeout
        ll=proxy.tail(logLines, raw=True)
        if isinstance(ll, dict): ll=serpent.tobytes(ll)
        ll=pickle.loads(ll)
        return [fmt.format(rec) for rec in ll]
    except (Pyro5.errors.TimeoutError,Pyro5.errors.CommunicationError):
        return [f'<TIMEOUT getting remote log from {remoteLogUri}>']
    except:
        log.exception("Error getting remote log (non-fatal)")
        return [f'<ERROR getting remote log from {remoteLogUri}>']


def _query_modelserver(name,uri,metadata,logLines,timeout) -> ModelserverInfo|None:
    if timeout<0: return None
    try:
        msrv = Pyro5.api.Proxy(uri)
        msrv._pyroTimeout=timeout
        msrv._pyroMaxRetries=1
        t0=time.time()
        ns = NsInfo(name=name,uri=uri,metadata=list(metadata))
        signature = msrv.getApplicationSignature()
        try:
            msi=ModelserverInfo(ns=ns,numJobs=ModelserverInfo.NumJobs(max=(se:=msrv.getStatusExtended()).maxJobs,curr=len(se.currJobs),total=se.totalJobs),jobs=se.currJobs,status=True,signature=signature)
        except AttributeError as e:
            log.exception('Error querying modelserver?:')
            msi=ModelserverInfo(ns=ns,numJobs=ModelserverInfo.NumJobs(max=-1,curr=len(jobs:=msrv.getStatus()),total=-1),jobs=jobs,status=False,signature=signature)
    except (Pyro5.errors.TimeoutError,Pyro5.errors.CommunicationError):
        return None
    timeout2=timeout-(time.time()-t0)
    if timeout2<0 or len(msi.jobs)==0 or logLines<1: return msi
    with concurrent.futures.ThreadPoolExecutor(len(msi.jobs),thread_name_prefix=f'mupif-modelserver-{name}-log') as exe:
        logs=list(exe.map(_query_job_log,*zip(*[(job.remoteLogUri,logLines,timeout2) for job in msi.jobs])))
    assert len(logs)==len(msi.jobs)
    for job,log_ in zip(msi.jobs,logs): job.tail=log_
    return msi


def jobmanInfo(ns, logLines=10, timeout=1) -> List[ModelserverInfo]:
    # create so that we don't change _pyroTimeout of the object passed
    ns2=Pyro5.api.Proxy(ns._pyroUri)
    t0=time.time()
    ns2._pyroTimeout=timeout
    ns2._pyroMaxRetries=1
    query=ns2.yplookup(meta_any={"type:jobmanager"})
    t1=time.time()
    with concurrent.futures.ThreadPoolExecutor(len(query),thread_name_prefix='mupif-modelservers-info') as exe:
        return list(exe.map(_query_modelserver,*zip(*[(name,uri,metadata,logLines,timeout-(t1-t0)) for name,(uri,metadata) in query.items()])))


class SchedulerInfo(BareData):
    """
    State of one scheduler registered in the nameserver (metadata ``type:scheduler``), as returned by :func:`schedulerInfo`.

    Built from the scheduler's ``getStatistics()``. Fields marked *optional* are reported only by
    schedulers of newer mupifDB versions (the refactored scheduler with load statistics); they
    are None or empty for older ones, so that readers can tell "unknown" from 0.
    """
    ns: NsInfo
    class NumTasks(BareData):
        """Current numbers of executions of the scheduler."""
        #: workflow processes running now
        running: int=0
        #: executions taken by the scheduler, not started yet
        scheduled: int=0
        #: executions which reached a final status (= finished + failed), in total
        processed: int=0
        finished: int=0
        failed: int=0
        #: percentage of the capacity in use
        currentLoad: float=0.
        #: (optional) executions waiting to run = pending + scheduled
        waiting: Optional[int]=None
        #: (optional) executions in the database queue (Pending); the queue is shared by all
        #: schedulers of a deployment, do not add it up over schedulers
        pending: Optional[int]=None
        #: (optional) executions Running according to the database (shared like pending); differs
        #: from running if some Running executions are not processes of the scheduler
        dbRunning: Optional[int]=None
        #: (optional) executions the scheduler can run at once
        capacity: Optional[int]=None
        #: drain mode: the scheduler takes no new executions
        draining: bool=False
    class History(BareData):
        """
        History of the scheduler, oldest period first, the last element is the current period.

        ``*48``: 48 periods of an hour, ``*120m``: 120 periods of a minute. ``pooled``,
        ``processed``, ``finished`` and ``failed`` count events in the period; ``load``,
        ``running`` and ``waiting`` are the peak level in the period (newer schedulers; older
        ones report the load at the last change in the period). Period *i* of *n* starts at
        ``periodStart - (n-1-i)*periodLength`` (seconds since the epoch).
        """
        pooledTasks48: List[int]=[]
        processedTasks48: List[int]=[]
        finishedTasks48: List[int]=[]
        failedTasks48: List[int]=[]
        load48: List[float]=[]
        #: (optional) peak running / waiting executions by hours
        running48: List[int]=[]
        waiting48: List[int]=[]
        #: (optional) peak running / waiting executions by minutes
        running120m: List[int]=[]
        waiting120m: List[int]=[]
        #: (optional) start of the current period (seconds since the epoch) and length of the periods (seconds)
        periodStart48: Optional[float]=None
        periodLength48: Optional[int]=None
        periodStart120m: Optional[float]=None
        periodLength120m: Optional[int]=None
    numTasks: NumTasks=NumTasks()
    history: History=History()
    class LastExecution(BareData):
        weid: str
        wid: str
        status: str
        started: str
        finished: Optional[str]
    lastExecutions: List[LastExecution]=[]
    class LogTail(BareData):
        tail: List[Any]
    running: Dict[str,LogTail]={}



def schedulerInfo(ns,timeout:float=5) -> List[SchedulerInfo|None]:
    """
    Query all schedulers registered in the nameserver (metadata ``type:scheduler``).

    :param ns: nameserver proxy
    :param timeout: time for the whole query in seconds
    :return: one entry per registered scheduler (None if it did not answer)
    """
    t0=time.time()
    ns2=Pyro5.api.Proxy(ns._pyroUri)
    ns2._pyroTimeout=timeout
    ns2._pyroMaxRetries=1
    query = ns2.yplookup(meta_any={"type:scheduler"})
    t1=time.time()
    with concurrent.futures.ThreadPoolExecutor(max(1,len(query)),thread_name_prefix='mupif-schedulers-info') as exe:
        return list(exe.map(_query_scheduler,*zip(*[(name,uri,metadata,timeout-(t1-t0)) for name,(uri,metadata) in query.items()])))


def _schedulerInfoFromStatistics(nsInfo:NsInfo,st:dict) -> SchedulerInfo:
    """
    Convert the result of a scheduler's ``getStatistics()`` to :class:`SchedulerInfo`.

    Keys of the original format are required; keys added later are read with defaults, so that
    schedulers of any version can be shown.
    """
    return SchedulerInfo(
        ns=nsInfo,
        numTasks=SchedulerInfo.NumTasks(running=st['runningTasks'], scheduled=st['scheduledTasks'], processed=st['processedTasks'], finished=st['finishedTasks'], failed=st['failedTasks'], currentLoad=st['currentLoad'],
            waiting=st.get('waitingTasks'), pending=st.get('pendingTasks'), dbRunning=st.get('dbRunningTasks'), capacity=st.get('capacity'), draining=bool(st.get('draining',False))),
        history=SchedulerInfo.History(pooledTasks48=st['pooledTasks48'], processedTasks48=st['processedTasks48'], finishedTasks48=st['finishedTasks48'], failedTasks48=st['failedTasks48'], load48=st['load48'],
            running48=st.get('running48',[]), waiting48=st.get('waiting48',[]), running120m=st.get('running120m',[]), waiting120m=st.get('waiting120m',[]),
            periodStart48=st.get('periodStart48'), periodLength48=st.get('periodLength48'), periodStart120m=st.get('periodStart120m'), periodLength120m=st.get('periodLength120m')),
        lastExecutions=[SchedulerInfo.LastExecution(weid=l[0], wid=l[1], status=l[2], started=l[3], finished=l[4]) for l in st['lastJobs']]
    )


def _query_scheduler(name,uri,metadata,timeout) -> SchedulerInfo|None:
    if timeout<0: return None
    t0=time.time()
    s = Pyro5.api.Proxy(uri)
    s._pyroTimeout=timeout
    s._pyroMaxRetries=1
    try:
        st=s.getStatistics()
    except (Pyro5.errors.TimeoutError,Pyro5.errors.CommunicationError):
        return None
    ret=_schedulerInfoFromStatistics(NsInfo(name=name,uri=uri,metadata=list(metadata)),st)
    t1=time.time()
    s._pyroTimeout=timeout-(t1-t0)
    if s._pyroTimeout<=0: return ret # no time to get live logs
    try:
        running=s.getExecutions(status='Running')
        if len(running)<1: return ret
        t1=time.time()
        weid_uri_timeout=[(r['_id'],r['loggerURI'],timeout-(t1-t0)) for r in running if ('_id' in r and 'loggerUri' in r)]
        with concurrent.futures.ThreadPoolExecutor(len(running),thread_name_prefix=f'mupif-scheduler-{name}-log') as exe:
            tails=list(exe.map(_query_scheduler_running_tail,*zip(*weid_uri_timeout)))
        for wut,tail in zip(weid_uri_timeout,tails):
            if tail is None: continue
            ret.running[wut[0]]=SchedulerInfo.LogTail(tail=tail)
    except (Pyro5.errors.TimeoutError,Pyro5.errors.CommunicationError):
        pass
    except:
        log.exception('Unable to get running executions from scheduler.')
    return ret


def _query_scheduler_running_tail(weid,logUri,timeout):
    # untested
    if timeout<0: return None
    proxy = Pyro5.api.Proxy(logUri)
    proxy._pyroTimeout = timeout
    proxy._pyroMaxRetries = 1
    rawTail = pickle.loads(serpent.tobytes(proxy.tail(10, raw=True)))
    return rawTail

    # proxy=
    #    ret.append(sch)
    #    if 'getExecutions' not in dir(s):
    #        log.warning('getExecutions not defined')
    #        continue  # old workflow monitor?
        # rr = {}
        # for ex in s.getExecutions(status='Running'):
        #     try:
        #         wf, lg = ex['workflowURI'], ex['loggerURI']
        #     except KeyError:
        #         continue
        #     try:
        #         proxy = Pyro5.api.Proxy(lg)
        #         proxy._pyroTimeout = 0.2
        #         rawTail = pickle.loads(serpent.tobytes(proxy.tail(10, raw=True)))
        #         rr[ex['_id']] = dict(tail=rawTail)
        #     except Pyro5.errors.CommunicationError:
        #         log.debug(f'Error getting tail of weid {ex["_id"]}, logger {lg}')
        # ret[-1]['running'] = rr
    #return ret


def vpnInfo(geoIpDb=None,hidePriv=True,isoTime=True):
    from ipaddress import ip_address, IPv6Address
    import subprocess
    import json
    import datetime
    import os.path

    rret = {}
    try:
        wgjson = json.loads(subprocess.check_output(['sudo', '/usr/share/doc/wireguard-tools/examples/json/wg-json']))
    except subprocess.CalledProcessError:
        warnings.warn('Calling wg-json failed. You might need to add the line "ALL ALL=NOPASSWD: /usr/share/doc/wireguard-tools/examples/json/wg-json" to /etc/sudoers.d/10-wireguard-show.conf (and run chmod 0440 /etc/sudoers.d/10-wireguard-show.conf) to get wireguard information as regular user.')
        return rret

    if not hidePriv:
        if geoIpDb:
            import GeoIP
            geoip = GeoIP.open(geoIpDb, GeoIP.GEOIP_STANDARD)

    for iface, dta in wgjson.items():
        ret = {}
        import netifaces
        ifaceip = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in ifaceip:
            ret['ipAddr'] = str(ip_address(ifaceip[netifaces.AF_INET][0]['addr']))
        elif netifaces.AF_INET6 in ifaceip:
            ret['ipAddr'] = str(ip_address(ifaceip[netifaces.AF_INET6][0]['addr']))
        else: ret['ipAddr'] = None
        activePeers = dict([(peerKey, peerData) for peerKey, peerData in dta['peers'].items() if 'transferRx' in peerData])
        ret['bytes'] = dict(tx=sum([p['transferTx'] for p in activePeers.values()]), rx=sum([p['transferRx'] for p in activePeers.values()]))
        ret['peers'] = []
        pubkey2name={}
        if os.path.exists(js:=os.path.expanduser(f'~/persistent/peers-{iface}.json')):
            pubkey2name=json.load(open(js,'r'))
        for peerKey, peerData in activePeers.items():
            lastHandshake = datetime.datetime.fromtimestamp(peerData.get('latestHandshake', 0))
            if isoTime: lastHandshake=lastHandshake.replace(microsecond=0).isoformat()
            peer = dict(
                vpnAddr=peerData['allowedIps'][0],
                bytes=dict(tx=peerData['transferTx'],rx=peerData['transferRx']),
                publicKey=peerKey,
                name=pubkey2name.get(peerKey,''),
                lastHandshake=lastHandshake,
                remote=None
            )
            if not hidePriv:
                pt = urllib.parse.urlsplit('//'+peerData['endpoint'])
                remote = dict(host=pt.hostname, port=pt.port)
                if geoIpDb:
                    gir = geoip.record_by_addr(pt.hostname)
                    remote['geoip'] = dict(country_code=gir['country_code'], country_name=gir['country_name'], city=gir['city'], longitude=gir['longitude'], latitude=gir['latitude'])
                peer['remote'] = remote
            ret['peers'].append(peer)
        rret[iface] = ret
    return rret


def nsInfo(ns=None):
    # jobMans=query=ns.yplookup(meta_any={"type:jobmanager"})
    import mupif as mp
    import os
    nshost, nsport, nssrc = mp.pyroutil.locateNameserver(return_src=True)
    if ns is None:
        ns = mp.pyroutil.connectNameserver(nshost, nsport)
    return dict(
        loc=dict(host=nshost, port=nsport, source=nssrc),
        names=ns.list(return_metadata=True),
        env=dict((k, v) for k, v in os.environ.items() if k.startswith('MUPIF_')),
    )


# def baseInfo():
#     import mupif as mp
#     import os
#     nshost, nsport, nssrc = mp.pyroutil.locateNameserver(return_src=True)


if __name__ == '__main__':
    def pprint(obj):
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.formatters import Terminal256Formatter
        import pprint
        print(highlight(pprint.pformat(obj), PythonLexer(), Terminal256Formatter()))
    import mupif as mp
    ns = mp.pyroutil.connectNameserver()
    pprint(schedulerInfo(ns))
    pprint(jobmanInfo(ns))
    pprint(vpnInfo(hidePriv=False))
    pprint(nsInfo())
