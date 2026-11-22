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
