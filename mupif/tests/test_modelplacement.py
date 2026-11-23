"""
Tests of finding and choosing model servers for the models of a workflow (execution profiles).

Everything here runs without a nameserver: the nameserver and the model servers are replaced by
small fakes, so that the tests are fast and deterministic.
"""
import dataclasses
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


# --- requirements from the workflow metadata ------------------------------------------------------

from mupif import modelplacement as mpl

WORKFLOW_MD = {
    'Models': [
        {'Name': 'thermal', 'Jobmanager': 'CVUT.demo01'},
        {'Name': 'mechanical', 'Jobmanager': 'CVUT.mech', 'ModelID': 'mech-1'},
        {'Name': 'local', 'Module': 'mymodule', 'Class': 'MyModel'},
        {'Name': 'later', 'Jobmanager': 'CVUT.demo01', 'Instantiate': False},
    ],
    'ExecutionProfiles': [
        {'Name': 'fast', 'Cost': '$', 'Description': '', 'Models': [
            {'Name': 'thermal', 'RequiredModelMetadata': {'Runtime_seconds'}, 'OptionalModelMetadata': ['Accuracy_High']},
        ]},
    ],
}


def test_modelRequirements_default():
    reqs = mpl.modelRequirements(WORKFLOW_MD)
    # local models are not placed on model servers
    assert set(reqs) == {'thermal', 'mechanical', 'later'}
    t = reqs['thermal']
    assert t.identity == {'CVUT.demo01'} and t.required == set() and t.optional == set()
    assert t.fallbackName == 'CVUT.demo01' and t.profile == 'default' and t.instantiate
    # ModelID widens the identity: any server serving model mech-1 is compatible
    assert reqs['mechanical'].identity == {'CVUT.mech', 'ModelID:mech-1'}
    assert not reqs['later'].instantiate


def test_modelRequirements_profile():
    reqs = mpl.modelRequirements(WORKFLOW_MD, 0)
    assert reqs['thermal'].required == {'Runtime_seconds'}
    assert reqs['thermal'].optional == {'Accuracy_High'}
    assert reqs['thermal'].profile == '#0 "fast"'
    # models not mentioned in the profile have no extra requirements
    assert reqs['mechanical'].required == set()
    # the cache key ignores optional tags (they do not change which servers are compatible)
    assert reqs['thermal'].key() != reqs['later'].key()
    assert mpl.modelRequirements(WORKFLOW_MD)['thermal'].key() == reqs['later'].key()
    with pytest.raises(ValueError):
        mpl.modelRequirements(WORKFLOW_MD, 1)
    # a workflow without profiles: only the default profile exists
    with pytest.raises(ValueError):
        mpl.modelRequirements({'Models': WORKFLOW_MD['Models']}, 0)


def test_modelRequirements_objects():
    # the scheduler passes database records (objects), not dicts
    md = types.SimpleNamespace(Models=[types.SimpleNamespace(Name='m', Jobmanager='CVUT.demo01', ModelID=None, Instantiate=None)], ExecutionProfiles=[])
    req = mpl.modelRequirements(md)['m']
    assert req.identity == {'CVUT.demo01'} and req.instantiate


# --- finding compatible servers --------------------------------------------------------------------

class FakeNS:
    'Nameserver stand-in: name -> (uri, tags), with the lookups used by modelplacement.'
    def __init__(self, entries):
        self.entries = entries

    def yplookup(self, meta_all=None, meta_any=None, return_metadata=True):
        return {n: (u, set(t)) for n, (u, t) in self.entries.items() if set(meta_all) <= set(t)}

    def lookup(self, name, return_metadata=False):
        import Pyro5.errors
        if name not in self.entries:
            raise Pyro5.errors.NamingError(f'unknown name: {name}')
        u, t = self.entries[name]
        return (u, set(t)) if return_metadata else u


def tags(*extra, base='CVUT.demo01', ID='demo01'):
    return {'type:jobmanager', base, f'ModelID:{ID}', *extra}


NS_ENTRIES = {
    # two instances of one model server
    'CVUT.demo01': ('PYRO:a@h1:1', tags('Runtime_seconds', 'Accuracy_Medium')),
    'CVUT.demo01~node2': ('PYRO:b@h2:1', tags('Runtime_seconds', 'Accuracy_High')),
    # the same model under another name
    'Other.demo01': ('PYRO:c@h3:1', tags('Runtime_minutes', base='Other.demo01')),
    # another model
    'CVUT.mech': ('PYRO:d@h4:1', tags(base='CVUT.mech', ID='mech-1')),
    # not a model server
    '1@CVUT.demo01': ('PYRO:e@h1:2', {'type:appserver'}),
}


def names(cands):
    return sorted(c.nsName for c in cands)


def test_findModelServers_instances():
    req = mpl.modelRequirements(WORKFLOW_MD)['thermal']
    assert names(mpl.findModelServers(FakeNS(NS_ENTRIES), req)) == ['CVUT.demo01', 'CVUT.demo01~node2']


def test_findModelServers_modelID():
    # with a ModelID, servers of that model under any name are compatible
    req = mpl.ModelRequirement(model='m', identity=frozenset({'CVUT.demo01', 'ModelID:demo01'}))
    assert names(mpl.findModelServers(FakeNS(NS_ENTRIES), req)) == ['CVUT.demo01', 'CVUT.demo01~node2', 'Other.demo01']


def test_findModelServers_requiredAndOptional():
    req = mpl.ModelRequirement(model='m', identity=frozenset({'ModelID:demo01'}), required=frozenset({'Runtime_seconds'}), optional=frozenset({'Accuracy_High'}))
    found = {c.nsName: c for c in mpl.findModelServers(FakeNS(NS_ENTRIES), req)}
    assert sorted(found) == ['CVUT.demo01', 'CVUT.demo01~node2']
    assert found['CVUT.demo01~node2'].score == 1 and found['CVUT.demo01'].score == 0
    assert found['CVUT.demo01~node2'].remoteTickets is False


def test_findModelServers_exactNameFallback():
    # a server registered without tags is still found by its exact name ...
    ns = FakeNS({'Old.server': ('PYRO:x@h:1', set())})
    req = mpl.ModelRequirement(model='m', identity=frozenset({'Old.server'}), fallbackName='Old.server')
    assert names(mpl.findModelServers(ns, req)) == ['Old.server']
    # ... but not when tags are required: they cannot be checked
    req = dataclasses.replace(req, required=frozenset({'Runtime_seconds'}))
    assert mpl.findModelServers(ns, req) == []
    # nothing registered at all
    assert mpl.findModelServers(FakeNS({}), mpl.ModelRequirement(model='m', identity=frozenset({'X'}), fallbackName='X')) == []


# --- ranking ---------------------------------------------------------------------------------------

def cand(name, score=0):
    return mpl.Candidate(nsName=name, uri=f'PYRO:{name}@h:1', tags=frozenset(), score=score)


def test_load():
    assert mpl.Load(free=1, max=4).used == 0.75
    assert mpl.Load(free=3).used is None
    assert mpl.Load(free=1, max=4).take().free == 0
    assert str(mpl.Load(free=1, max=4)) == '1 free of 4'


def test_rank_leastLoadedFirst():
    loads = {'a': mpl.Load(free=1, max=4), 'b': mpl.Load(free=2, max=2), 'c': mpl.Load(free=3, max=10)}
    # used share: a 75 %, b 0 %, c 70 %: less loaded first, although c has more free slots than b
    assert [c.nsName for c in mpl.rankCandidates([cand('a'), cand('b'), cand('c')], loads)] == ['b', 'c', 'a']


def test_rank_freeThenScoreThenLoad():
    loads = {'full': mpl.Load(free=0, max=1), 'busy': mpl.Load(free=1, max=10), 'idle': mpl.Load(free=4, max=4),
             'old': mpl.Load(free=5), 'gone': None}
    ranked = mpl.rankCandidates([cand('full', score=2), cand('busy', score=1), cand('idle'), cand('old'), cand('gone', score=5)], loads)
    # unreachable left out; full servers last whatever their score; a preferred server before
    # a less loaded one; servers not reporting their capacity after those which do
    assert [c.nsName for c in ranked] == ['busy', 'idle', 'old', 'full']


def test_rank_randomTieBreak():
    import random
    loads = {'a': mpl.Load(free=2, max=2), 'b': mpl.Load(free=2, max=2)}
    rng = random.Random(1)
    firsts = {mpl.rankCandidates([cand('a'), cand('b')], loads, rng)[0].nsName for _ in range(50)}
    # equally loaded servers are chosen at random, so that simultaneous starts spread over them
    assert firsts == {'a', 'b'}


# --- allocation with fallback ----------------------------------------------------------------------

REQ = mpl.ModelRequirement(model='thermal', identity=frozenset({'CVUT.demo01'}))


def allocator(outcomes):
    'allocate() stand-in: server name -> exception to raise, or the value to return.'
    tried = []

    def allocate(c):
        tried.append(c.nsName)
        out = outcomes[c.nsName]
        if isinstance(out, BaseException):
            raise out
        return out
    return allocate, tried


def test_allocate_firstAccepts():
    allocate, tried = allocator({'a': 'model@a', 'b': 'model@b'})
    model, placement = mpl.allocateOnCandidates(REQ, [cand('a'), cand('b')], allocate)
    assert (model, placement.nsName, placement.skipped, tried) == ('model@a', 'a', [], ['a'])


def test_allocate_fallsBack(caplog):
    import Pyro5.errors
    allocate, tried = allocator({'a': mp.modelserverbase.ModelServerNoResourcesException('full'),
                                 'b': Pyro5.errors.CommunicationError('connection refused'),
                                 'c': 'model@c'})
    with caplog.at_level('INFO', logger='mupif.modelplacement'):
        model, placement = mpl.allocateOnCandidates(REQ, [cand('a'), cand('b'), cand('c')], allocate)
    assert model == 'model@c' and placement.nsName == 'c'
    assert [n for n, _ in placement.skipped] == ['a', 'b']
    assert placement.skipped[0][1] == 'no free slot'
    # the log tells where the model went and why the others were skipped
    assert 'Model thermal allocated on model server c (after skipping a, b)' in caplog.text
    assert 'model server a did not accept the model (no free slot)' in caplog.text


def test_allocate_allFull():
    import Pyro5.errors
    # the no-resources exception may arrive as a generic Pyro error naming the class
    pyroForm = Pyro5.errors.PyroError('Error serializing exception: mupif.modelserverbase.ModelServerNoResourcesException')
    allocate, _ = allocator({'a': pyroForm, 'b': Pyro5.errors.CommunicationError('down')})
    with pytest.raises(mp.modelserverbase.ModelServerNoResourcesException):
        mpl.allocateOnCandidates(REQ, [cand('a'), cand('b')], allocate)


def test_allocate_noneAccepts():
    import Pyro5.errors
    allocate, _ = allocator({'a': Pyro5.errors.CommunicationError('down')})
    with pytest.raises(RuntimeError):
        mpl.allocateOnCandidates(REQ, [cand('a')], allocate)
    with pytest.raises(RuntimeError, match='No model server compatible'):
        mpl.allocateOnCandidates(REQ, [], allocate)


# --- the workflow side -----------------------------------------------------------------------------

class ProfiledWorkflow(mp.Workflow):
    def __init__(self, metadata=None):
        super().__init__(metadata={'Name': 'wf', 'ID': 'wf', 'Description': '', 'Inputs': [], 'Outputs': [],
                                   'Models': WORKFLOW_MD['Models'], 'ExecutionProfiles': WORKFLOW_MD['ExecutionProfiles']})
        self.updateMetadata(metadata)


def test_workflow_profileSelection():
    wf = ProfiledWorkflow()
    # no profile selected: the default one
    assert wf.getExecutionProfileIndex() == -1
    assert wf._modelRequirements()['thermal'].required == set()
    wf = ProfiledWorkflow(metadata={'Execution': {'ExecutionProfileIndex': 0}})
    assert wf.getExecutionProfileIndex() == 0
    assert wf._modelRequirements()['thermal'].required == {'Runtime_seconds'}
    assert wf.getModelServers() == {}


def test_workflow_unknownProfile():
    # an execution profile the workflow does not have is an error before anything is allocated
    wf = ProfiledWorkflow(metadata={'Execution': {'ExecutionProfileIndex': 3}})
    with pytest.raises(ValueError, match='Execution profile #3'):
        wf._allocateAllModels()


# --- connecting by metadata ------------------------------------------------------------------------

def test_connectModelServerWithMetadata(monkeypatch):
    loads = {'PYRO:a@h1:1': mpl.Load(free=1, max=4), 'PYRO:b@h2:1': mpl.Load(free=4, max=4), 'PYRO:c@h3:1': mpl.Load(free=2, max=2)}
    monkeypatch.setattr(mpl, 'serverLoad', lambda uri, timeout=5.: loads.get(uri))
    connected = []

    def connectApp(ns, name):
        connected.append(name)
        if name == 'CVUT.demo01~node2':
            raise RuntimeError('does not answer')
        return f'proxy:{name}'
    monkeypatch.setattr(pyroutil, '_connectApp', connectApp)
    monkeypatch.setattr(mp.modelserverbase, 'RemoteModelServer', lambda proxy: proxy)
    ns = FakeNS(NS_ENTRIES)
    # instances of CVUT.demo01: node2 is idle but does not answer, so the other one
    assert pyroutil.connectModelServerWithMetadata(ns, {'CVUT.demo01'}) == 'proxy:CVUT.demo01'
    assert connected == ['CVUT.demo01~node2', 'CVUT.demo01']
    # any server of model demo01, preferring Runtime_minutes: Other.demo01, though busier than node2
    connected.clear()
    assert pyroutil.connectModelServerWithMetadata(ns, {'ModelID:demo01'}, {'Runtime_minutes'}) == 'proxy:Other.demo01'
    with pytest.raises(RuntimeError):
        pyroutil.connectModelServerWithMetadata(ns, {'No.such.server'})
