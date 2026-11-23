"""
Tests of finding and choosing model servers for the models of a workflow (execution profiles).

Everything here runs without a nameserver: the nameserver and the model servers are replaced by
small fakes, so that the tests are fast and deterministic.
"""
import types

import pytest

import mupif as mp
from mupif import pyroutil


def fakeModelServer(name='CVUT.demo01', ID='demo01', accuracy='High', robustness='Medium', comptime=30., remoteTickets=True):
    'Stand-in for a model server: just what modelServerTags reads.'
    md = {'ID': ID, 'Solver': {'Accuracy': accuracy, 'Robustness': robustness, 'Estim_comp_time_s': comptime}}
    return types.SimpleNamespace(getName=lambda: name, getModelMetadata=lambda: md, remoteTickets=remoteTickets)


def test_modelServerTags():
    tags = pyroutil.modelServerTags(fakeModelServer())
    assert tags == {'type:jobmanager', 'CVUT.demo01', 'ModelID:demo01', 'Accuracy_High', 'Robustness_Medium', 'Runtime_seconds', 'mupif:tickets-v2'}


def test_modelServerTags_withoutIdAndTickets():
    # a model without ID gets no ModelID tag; a server without working tickets does not advertise them
    tags = pyroutil.modelServerTags(fakeModelServer(ID='', comptime=7200, remoteTickets=False))
    assert 'Runtime_hours' in tags
    assert not any(t.startswith('ModelID:') for t in tags)
    assert 'mupif:tickets-v2' not in tags


def test_modelInWorkflowMeta_ModelID():
    # a remote model may be given by its model ID instead of a model server name
    m = mp.meta.ModelInWorkflowMeta(Name='m', ModelID='demo01')
    assert m.Jobmanager == '' and m.ModelID == 'demo01'
    mp.meta.ModelInWorkflowMeta(Name='m', Jobmanager='CVUT.demo01')
    with pytest.raises(ValueError):
        mp.meta.ModelInWorkflowMeta(Name='m')
