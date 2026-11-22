"""Tests of the scheduler part of :mod:`mupif.monitor` (no nameserver or scheduler needed)."""

from mupif import monitor

#: getStatistics() of a scheduler before the load statistics (original format)
OLD = dict(runningTasks=1, scheduledTasks=2, processedTasks=10, finishedTasks=8, failedTasks=2, currentLoad=33.,
           lastJobs=[['e1', 'w1', 'Running', '2026-01-01T10:00:00', None]],
           pooledTasks48=[0] * 48, processedTasks48=[0] * 48, finishedTasks48=[0] * 48, failedTasks48=[0] * 48, load48=[0.] * 48)
#: getStatistics() of a scheduler with the load statistics (mupifDB scheduler refactoring)
NEW = dict(OLD, draining=True, capacity=3, waitingTasks=7, pendingTasks=5, dbRunningTasks=2,
           running48=[1] * 48, waiting48=[7] * 48, running120m=[1] * 120, waiting120m=[7] * 120,
           periodStart48=3600. * 1000, periodLength48=3600, periodStart120m=60. * 60000, periodLength120m=60)
NS = monitor.NsInfo(name='mupif.scheduler', uri='PYRO:obj@host:1', metadata=['type:scheduler'])


def test_old_format():
    """Statistics of an older scheduler are read; the load fields are unknown (None/empty), not 0."""
    si = monitor._schedulerInfoFromStatistics(NS, OLD)
    assert (si.numTasks.running, si.numTasks.scheduled, si.numTasks.processed) == (1, 2, 10)
    assert si.numTasks.waiting is None and si.numTasks.capacity is None and si.numTasks.draining is False
    assert si.history.running48 == [] and si.history.periodStart48 is None
    assert si.lastExecutions[0].weid == 'e1'


def test_new_format():
    """Statistics with the load fields are read completely and survive serialization (as served by the API)."""
    si = monitor._schedulerInfoFromStatistics(NS, NEW)
    assert (si.numTasks.waiting, si.numTasks.pending, si.numTasks.dbRunning, si.numTasks.capacity, si.numTasks.draining) == (7, 5, 2, 3, True)
    assert len(si.history.running120m) == 120 and si.history.waiting48[-1] == 7
    assert (si.history.periodStart120m, si.history.periodLength120m) == (60. * 60000, 60)
    data = si.model_dump(mode='json')
    assert monitor.SchedulerInfo.model_validate(data) == si


class _Proxy:
    """Stand-in for a Pyro proxy of a scheduler: getStatistics() returns *stats* or raises it."""
    behaviour = None

    def __init__(self, uri):
        self._pyroMethods = {'getStatistics'}

    def getStatistics(self):
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        return self.behaviour


def _query(monkeypatch, behaviour):
    monkeypatch.setattr(monitor.Pyro5.api, 'Proxy', _Proxy)
    monkeypatch.setattr(_Proxy, 'behaviour', behaviour)
    return monitor._query_scheduler('mupif.scheduler', 'PYRO:obj@host:1', ['type:scheduler'], 5)


def test_query_available(monkeypatch):
    """A scheduler which answers is available; one without getExecutions() is not an error (no log tails)."""
    si = _query(monkeypatch, NEW)
    assert si.available and si.error is None and si.numTasks.waiting == 7 and si.running == {}


def test_query_unreachable_is_reported_by_name(monkeypatch):
    """A registered scheduler which does not answer is listed with its name and the reason (it used to be None)."""
    import Pyro5.errors
    si = _query(monkeypatch, Pyro5.errors.CommunicationError('connection refused'))
    assert not si.available and si.ns.name == 'mupif.scheduler' and 'connection refused' in si.error
    assert si.numTasks.running == 0


def test_query_scheduler_error_does_not_break_the_query(monkeypatch):
    """An exception raised by the scheduler (e.g. a bug) makes it unavailable instead of failing the whole query."""
    si = _query(monkeypatch, RuntimeError('Traveling to the past?'))
    assert not si.available and 'Traveling to the past?' in si.error


def test_query_without_time_left():
    """No time left after the nameserver lookup: the scheduler is reported as not queried."""
    si = monitor._query_scheduler('mupif.scheduler', 'PYRO:obj@host:1', [], -1)
    assert not si.available and 'not queried' in si.error
