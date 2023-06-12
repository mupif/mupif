# from .pyroutil import connectNameserver
import Pyro5.api
import urllib.parse
import warnings
import pickle
import logging
import serpent

log = logging.getLogger()


def jobmanInfo(ns, logLines=10):
    query = ns.yplookup(meta_any={"type:jobmanager"})
    ret = []
    for name, (uri, metadata) in query.items():
        jobman = Pyro5.api.Proxy(uri)
        jm = {}
        jm['ns'] = dict(name=name, uri=uri, metadata=metadata)
        try:
            se = jobman.getStatusExtended()
            jm['numJobs'] = dict(max=se.get('maxJobs', -1), curr=len(se['currJobs']), total=se['totalJobs'])
            jm['jobs'] = se['currJobs']
        except AttributeError:
            jm['jobs'] = jobman.getStatus()
            jm['numJobs'] = dict(max=-1, curr=len(jm['jobs']), total=-1)
        for job in jm['jobs']:
            fmt = logging.Formatter(fmt='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')
            if 'remoteLogUri' in job:
                ll = Pyro5.api.Proxy(job['remoteLogUri']).tail(logLines, raw=True)
                if isinstance(ll, dict):
                    ll = serpent.tobytes(ll)
                ll=pickle.loads(ll)
                job['tail'] = [fmt.format(rec) for rec in ll]
        jm['signature'] = jobman.getApplicationSignature()
        ret.append(jm)
    return ret


def schedulerInfo(ns):
    query = ns.yplookup(meta_any={"type:scheduler"})
    ret = []
    for name, (uri, metadata) in query.items():
        sch = {}
        sch['ns'] = dict(name=name, uri=uri, metadata=metadata)
        s = Pyro5.api.Proxy(uri)
        st = s.getStatistics()
        sch['numTasks'] = dict(running=st['runningTasks'], scheduled=st['scheduledTasks'], processed=st['processedTasks'], finished=st['finishedTasks'], failed=st['failedTasks'], currentLoad=st['currentLoad'])
        sch['history'] = dict(pooledTasks48=st['pooledTasks48'], processedTasks48=st['processedTasks48'], finishedTasks48=st['finishedTasks48'], failedTasks48=st['failedTasks48'], load48=st['load48'])
        sch['lastExecutions'] = [dict(weid=l[0], wid=l[1], status=l[2], started=l[3], finished=l[4]) for l in st['lastJobs']]
        ret.append(sch)
        if 'getExecutions' not in dir(s):
            log.warning('getExecutions not defined')
            continue  # old workflow monitor?
        rr = {}
        for ex in s.getExecutions(status='Running'):
            try:
                wf, lg = ex['workflowURI'], ex['loggerURI']
            except KeyError:
                continue
            try:
                rawTail = pickle.loads(serpent.tobytes(Pyro5.api.Proxy(lg).tail(10, raw=True)))
                rr[ex['_id']] = dict(tail=rawTail)
            except Pyro5.errors.CommunicationError:
                log.debug(f'Error getting tail of weid {ex["_id"]}, logger {lg}')
        ret[-1]['running'] = rr
    return ret


def vpnInfo(geoIpDb=None,hidePriv=True):
    from ipaddress import ip_address, IPv6Address
    import subprocess
    import json
    import datetime

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
        for peerKey, peerData in activePeers.items():
            peer = dict(
                vpnAddr=peerData['allowedIps'][0],
                bytes=dict(tx=peerData['transferTx'], rx=peerData['transferRx']),
                publicKey=peerKey,
                lastHandshake=datetime.datetime.fromtimestamp(peerData.get('latestHandshake', 0)),
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
