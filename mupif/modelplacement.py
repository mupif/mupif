#
#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2026 Borek Patzak
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
#
"""
Placement of workflow models on model servers: execution profiles, compatible servers, load.

A remote model of a workflow is allocated on a *model server* (jobmanager). Several model servers
may be able to serve it:

* several **instances** of one model server (same base name, e.g. on different hosts), registered
  under distinct nameserver names (see :func:`mupif.pyroutil.modelServerNSName`);
* model servers registered under **different names** which serve the same model (same model ID).

Every model server registration carries tags (see :func:`mupif.pyroutil.modelServerTags`):
``type:jobmanager``, its base name, ``ModelID:<id>``, ``Accuracy_*``, ``Robustness_*``,
``Runtime_*``. This module finds the servers compatible with a model by these tags and ranks them;
the workflow then allocates the model on the best one, falling back to the next ones.

**Requirements** (:class:`ModelRequirement`) come from the workflow metadata:

* *identity* -- a server is compatible if it carries the model's ``Jobmanager`` name (all
  instances of that model server, including servers of older mupif versions, which already carry
  their name as a tag) or, if the model gives ``ModelID``, the tag ``ModelID:<ModelID>``;
* *required* tags -- from the ``RequiredModelMetadata`` of the selected execution profile: a
  server must carry all of them;
* *optional* tags -- from ``OptionalModelMetadata`` of the profile: servers carrying more of them
  are preferred.

**Execution profiles** (``WorkflowMeta.ExecutionProfiles``) are selected by
``Execution.ExecutionProfileIndex``; a negative index selects the **default profile**, which has
no required or optional tags: any compatible server, the least loaded first. A workflow without
profiles, whose models give only ``Jobmanager``, behaves as before when a single server of that
name runs.

**Execution servers** (:mod:`mupif.executionserver`) run any model package of a registry, given by
its model ID. A model with ``ModelID`` (optionally pinned by ``ModelVersion``) may run on every
execution server carrying the required tags, besides the model servers above. Execution servers do
not carry the profile's model tags (``Accuracy_*`` etc. describe one model; an execution server runs
many), so a profile *requiring* such tags excludes them. Whether an execution server can really run
the model (runtime, host capabilities) it decides itself: if not, it refuses at once
(:class:`~mupif.modelserverbase.ModelServerCannotRunException`) and the next server is tried. An
execution server on which the model is *ready* (prepared before) carries ``ModelID:<id>`` (and
``ModelID:<id>@<version>``): the model starts there at once, elsewhere its package is downloaded and
its environment installed first.

**Ranking** (:func:`rankCandidates`): servers with a free slot before full ones; then model servers
before execution servers on which the model is ready, before other execution servers (where the
model would be prepared first); then by the number of optional tags matched (more first), then by
load (the used share of its job slots, lower first), random among equal ones, so that workflows
starting at the same time spread over equally loaded servers.

**Allocation** (:func:`allocateOnCandidates`): the model is allocated on the first server of the
ranking which accepts it. A server which is full (another client took the last slot meanwhile) or
unreachable is skipped. If no server accepts the model and at least one was only full, a
:class:`~mupif.modelserverbase.ModelServerNoResourcesException` is raised, so that the caller can
retry later (the mupifDB scheduler returns the execution to its queue).

The functions take the nameserver and model servers as arguments (or functions), so that they are
used both by :class:`mupif.Workflow` and by the mupifDB scheduler (which checks the capacity before
starting a workflow) and tested without a running nameserver.
"""

from __future__ import annotations

import dataclasses
import logging
import random
from typing import Any, Callable, Iterable, Optional, TypeVar

import Pyro5.api
import Pyro5.errors

from . import modelserverbase

log = logging.getLogger(__name__)

#: nameserver tag of model server registrations (see :class:`mupif.pyroutil._NS_METADATA`)
JOBMANAGER_TAG = 'type:jobmanager'
#: prefix of the tag carrying the model ID of a model server
MODEL_ID_TAG = 'ModelID:'
#: tag of model servers whose preAllocate tickets work remotely
TICKETS_TAG = 'mupif:tickets-v2'
#: nameserver tag of execution server registrations (see :mod:`mupif.executionserver`)
EXECUTION_SERVER_TAG = 'type:executionserver'

#: fully qualified name of the exception a model server raises when it has no free job slot
NO_RESOURCES_EXCEPTION = 'mupif.modelserverbase.ModelServerNoResourcesException'
#: fully qualified name of the exception an execution server raises when it cannot run a model
CANNOT_RUN_EXCEPTION = 'mupif.modelserverbase.ModelServerCannotRunException'


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Read *key* from a dict or an attribute of an object (pydantic model, namespace)."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclasses.dataclass(frozen=True)
class ModelRequirement:
    """
    What a model server must offer to serve one model of a workflow (see the module documentation).
    """
    #: name of the model in the workflow (``Models[].Name``)
    model: str
    #: tags any one of which makes a server compatible: the ``Jobmanager`` base name, ``ModelID:<id>``
    identity: frozenset[str]
    #: tags a server must all carry (``RequiredModelMetadata`` of the profile)
    required: frozenset[str] = frozenset()
    #: tags preferring a server (``OptionalModelMetadata`` of the profile)
    optional: frozenset[str] = frozenset()
    #: nameserver name looked up exactly when no server is found by tags (the ``Jobmanager`` name):
    #: servers registered without tags (very old ones) are still found
    fallbackName: Optional[str] = None
    #: whether the model is allocated when the workflow is initialized (``Instantiate``)
    instantiate: bool = True
    #: execution profile the requirement comes from, for messages: ``default`` or ``#1 "name"``
    profile: str = 'default'
    #: model ID (``ModelID``): execution servers are compatible too, and are asked for this model
    modelID: Optional[str] = None
    #: model package version (``ModelVersion``); None: the latest one
    modelVersion: Optional[str] = None

    def key(self) -> tuple:
        """
        Return a hashable key of what decides compatibility (not the optional tags, which only rank).

        Models with equal keys have the same compatible servers; used to cache lookups.
        """
        return (self.identity, self.required, self.fallbackName, self.modelID, self.modelVersion)

    def readyTag(self) -> Optional[str]:
        """Return the tag of execution servers on which the model is ready (None without a model ID)."""
        if not self.modelID:
            return None
        return MODEL_ID_TAG + self.modelID + (f'@{self.modelVersion}' if self.modelVersion else '')

    def describe(self) -> str:
        """Return a short human-readable description, for logs."""
        parts = ['any of ' + ', '.join(sorted(self.identity))]
        if self.modelID:
            parts.append(f'or an execution server running {self.modelID}' + (f'@{self.modelVersion}' if self.modelVersion else ''))
        if self.required:
            parts.append('required ' + ', '.join(sorted(self.required)))
        if self.optional:
            parts.append('preferred ' + ', '.join(sorted(self.optional)))
        return f'profile {self.profile}: ' + '; '.join(parts)


def profileName(metadata: Any, profileIndex: int) -> str:
    """Return the description of an execution profile used in messages: ``default`` or ``#<index> "<Name>"``."""
    if profileIndex is None or profileIndex < 0:
        return 'default'
    profiles = _get(metadata, 'ExecutionProfiles') or []
    name = _get(profiles[profileIndex], 'Name', '') if profileIndex < len(profiles) else ''
    return f'#{profileIndex} "{name}"'


def modelRequirements(metadata: Any, profileIndex: int = -1) -> dict[str, ModelRequirement]:
    """
    Return the requirements of the remote models of a workflow under an execution profile.

    :param metadata: workflow metadata (dict or object) with ``Models`` and optionally
                     ``ExecutionProfiles``; entries may be dicts or objects
    :param profileIndex: index into ``ExecutionProfiles``; negative: the default profile
    :return: model name -> requirement, for every model with ``Jobmanager`` or ``ModelID`` (local
             models, given by ``Module``/``Class``, are left out); models with ``Instantiate``
             false are included, marked by :attr:`ModelRequirement.instantiate`
    :raises ValueError: if *profileIndex* does not select a profile of the workflow
    """
    if profileIndex is None:
        profileIndex = -1
    profileModels: dict[str, Any] = {}
    if profileIndex >= 0:
        profiles = _get(metadata, 'ExecutionProfiles') or []
        if profileIndex >= len(profiles):
            raise ValueError(f'Execution profile #{profileIndex} requested, but the workflow has {len(profiles)} execution profile(s).')
        profileModels = {_get(m, 'Name'): m for m in (_get(profiles[profileIndex], 'Models') or [])}
    profile = profileName(metadata, profileIndex)
    ret = {}
    for m in _get(metadata, 'Models') or []:
        name = _get(m, 'Name', '')
        jobmanager = _get(m, 'Jobmanager', '') or ''
        modelID = _get(m, 'ModelID', '') or ''
        modelVersion = _get(m, 'ModelVersion', '') or ''
        if not jobmanager and not modelID:
            continue
        identity = set()
        if jobmanager:
            identity.add(jobmanager)
        if modelID:
            identity.add(MODEL_ID_TAG + str(modelID))
        pm = profileModels.get(name)
        instantiate = _get(m, 'Instantiate', True)
        ret[name] = ModelRequirement(
            model=name,
            identity=frozenset(identity),
            required=frozenset(_get(pm, 'RequiredModelMetadata', None) or ()) if pm is not None else frozenset(),
            optional=frozenset(_get(pm, 'OptionalModelMetadata', None) or ()) if pm is not None else frozenset(),
            fallbackName=jobmanager or None,
            instantiate=True if instantiate is None else bool(instantiate),
            profile=profile,
            modelID=str(modelID) if modelID else None,
            modelVersion=str(modelVersion) if modelVersion else None,
        )
    return ret


@dataclasses.dataclass(frozen=True)
class Candidate:
    """A model server compatible with a model (see :func:`findModelServers`)."""
    #: name of the server's nameserver registration (unique per instance)
    nsName: str
    #: Pyro URI of the server
    uri: str
    #: tags of the registration
    tags: frozenset[str]
    #: number of optional tags of the requirement the server carries
    score: int = 0
    #: an execution server (asked for the model by its ID), not a model server of the model
    isExecutionServer: bool = False
    #: (execution servers) the model is ready there: it starts at once
    ready: bool = False

    @property
    def tier(self) -> int:
        """Preference by kind of server (lower first): model server 0, execution server with the model ready 1, other execution server 2."""
        if not self.isExecutionServer:
            return 0
        return 1 if self.ready else 2

    def describe(self) -> str:
        """Return the name, marked if it is an execution server, for logs."""
        if not self.isExecutionServer:
            return self.nsName
        return f'{self.nsName} [execution server, model {"ready" if self.ready else "to be prepared"}]'

    @property
    def remoteTickets(self) -> bool:
        """Whether the server's preAllocate tickets work remotely (see :data:`TICKETS_TAG`)."""
        return TICKETS_TAG in self.tags


def findModelServers(ns, req: ModelRequirement) -> list[Candidate]:
    """
    Find the registered model servers compatible with a model.

    A server is compatible if its registration carries ``type:jobmanager``, one of the identity
    tags and all required tags. If no such server is found by tags and the requirement has no
    required tags, the exact name :attr:`ModelRequirement.fallbackName` is looked up, so that a
    server registered without tags is found as before. If the model has a model ID, every execution
    server carrying the required tags is compatible too (see the module documentation).

    :param ns: nameserver proxy (owned by the calling thread)
    :param req: requirement of the model
    :return: compatible servers, in no particular order (see :func:`rankCandidates`)
    """
    found: dict[str, Candidate] = {}
    for ident in sorted(req.identity):
        res = ns.yplookup(meta_all={JOBMANAGER_TAG, ident, *req.required}, return_metadata=True)
        for name, (uri, tags) in res.items():
            tags = frozenset(tags or ())
            found[name] = Candidate(nsName=name, uri=str(uri), tags=tags, score=len(tags & req.optional))
    if not found and req.fallbackName and not req.required:
        try:
            uri, tags = ns.lookup(req.fallbackName, return_metadata=True)
        except Pyro5.errors.NamingError:
            pass
        else:
            tags = frozenset(tags or ())
            found[req.fallbackName] = Candidate(nsName=req.fallbackName, uri=str(uri), tags=tags, score=len(tags & req.optional))
    if req.modelID:
        readyTag = req.readyTag()
        res = ns.yplookup(meta_all={EXECUTION_SERVER_TAG, *req.required}, return_metadata=True)
        for name, (uri, tags) in res.items():
            if name in found:
                continue
            tags = frozenset(tags or ())
            found[name] = Candidate(nsName=name, uri=str(uri), tags=tags, score=len(tags & req.optional), isExecutionServer=True, ready=readyTag in tags)
    return list(found.values())


@dataclasses.dataclass(frozen=True)
class Load:
    """Free and total job slots of a model server."""
    #: jobs the server can allocate now
    free: int
    #: maximum number of jobs (None: not reported by the server)
    max: Optional[int] = None

    @property
    def used(self) -> Optional[float]:
        """Used share of the job slots, 0…1 (None if :attr:`max` is unknown)."""
        if not self.max:
            return None
        return min(1., max(0., (self.max - self.free) / self.max))

    def take(self, n: int = 1) -> 'Load':
        """Return the load after *n* more jobs were allocated (for bookkeeping before allocating)."""
        return dataclasses.replace(self, free=self.free - n)

    def __str__(self):
        return f'{self.free} free' + (f' of {self.max}' if self.max else '')


def serverLoad(uri: str, timeout: float = 5., logLevel: int = logging.WARNING) -> Optional[Load]:
    """
    Ask a model server for its free and total job slots.

    :param uri: Pyro URI of the server
    :param timeout: seconds to wait for the answer
    :param logLevel: level of the message when the server cannot be reached (a long-running caller
                     asking repeatedly, such as the mupifDB scheduler, reports it once itself)
    :return: the load, or None if the server cannot be reached
    """
    try:
        proxy = Pyro5.api.Proxy(uri)
        proxy._pyroTimeout = timeout
        proxy._pyroMaxRetries = 1
        free = int(proxy.getNumberOfFreeJobs())
    except Exception as e:
        log.log(logLevel, f'Cannot get the free job slots of model server {uri}: {e}')
        return None
    try:
        status = proxy.getStatusExtended()
        mx = _get(status, 'maxJobs')
        return Load(free=free, max=int(mx) if mx else None)
    except Exception:
        # older model servers do not report their capacity: rank them by free slots only
        return Load(free=free)


def rankCandidates(candidates: Iterable[Candidate], loads: dict[str, Optional[Load]], rng: Optional[random.Random] = None) -> list[Candidate]:
    """
    Order compatible servers from the best to the worst choice; unreachable ones are left out.

    Order: servers with a free slot first; then by :attr:`Candidate.tier` (model servers, execution
    servers with the model ready, other execution servers); then by :attr:`Candidate.score`
    (optional tags matched, more first); then by the used share of job slots (lower first; servers
    not reporting their capacity after those which do, the more free slots first); random among
    equal ones.

    :param candidates: compatible servers
    :param loads: server name -> load, None if unreachable (servers missing here are left out too)
    :param rng: random generator for the tie-break (default: the module :mod:`random`)
    :return: reachable servers, best first
    """
    rnd = rng or random

    def key(c: Candidate):
        load = loads[c.nsName]
        assert load is not None
        return (load.free <= 0, c.tier, -c.score, load.used if load.used is not None else 1., -load.free, rnd.random())
    return sorted((c for c in candidates if loads.get(c.nsName) is not None), key=key)


def _isRemoteError(err: BaseException | None, cls: type, qualName: str) -> bool:
    """
    Tell whether *err* (or an exception it was raised from) is *cls*, also in the form it may arrive over Pyro.

    Over Pyro, the exception may arrive as a generic :class:`Pyro5.errors.PyroError` (Pyro fails to
    serialize it) whose message or remote traceback names the class (*qualName*); both forms are
    recognized, also when chained.
    """
    seen = set()
    while err is not None and id(err) not in seen:
        seen.add(id(err))
        if isinstance(err, cls):
            return True
        remoteTraceback = ''.join(getattr(err, '_pyroTraceback', None) or [])
        if qualName in str(err) or qualName in remoteTraceback:
            return True
        err = err.__cause__ or err.__context__
    return False


def isNoResourcesError(err: BaseException | None) -> bool:
    """
    Tell whether *err* means "model server has no free slot" (:class:`~mupif.modelserverbase.ModelServerNoResourcesException`).

    Recognized also in the forms it arrives over Pyro (see :func:`_isRemoteError`).
    """
    return _isRemoteError(err, modelserverbase.ModelServerNoResourcesException, NO_RESOURCES_EXCEPTION)


def isCannotRunError(err: BaseException | None) -> bool:
    """
    Tell whether *err* means "the server cannot run this model" (:class:`~mupif.modelserverbase.ModelServerCannotRunException`).

    Recognized also in the forms it arrives over Pyro (see :func:`_isRemoteError`).
    """
    return _isRemoteError(err, modelserverbase.ModelServerCannotRunException, CANNOT_RUN_EXCEPTION)


@dataclasses.dataclass
class Placement:
    """Where a model was allocated, and the servers tried before (for logs and records)."""
    #: model name in the workflow
    model: str
    #: registered name of the server the model runs on
    nsName: str
    #: execution profile (see :attr:`ModelRequirement.profile`)
    profile: str = 'default'
    #: servers tried before, which did not accept the model: (name, reason)
    skipped: list[tuple[str, str]] = dataclasses.field(default_factory=list)


T = TypeVar('T')


def allocateOnCandidates(req: ModelRequirement, ranked: list[Candidate], allocate: Callable[[Candidate], T], loads: Optional[dict[str, Optional[Load]]] = None) -> tuple[T, Placement]:
    """
    Allocate a model on the first server of *ranked* which accepts it.

    Every attempt is logged, so that the execution log shows which server was chosen and why the
    servers before it were skipped.

    :param req: requirement of the model (for messages)
    :param ranked: compatible servers, best first (see :func:`rankCandidates`)
    :param allocate: allocates the model on a server and returns it; raises if the server cannot
    :param loads: loads of the servers (only for the log message)
    :return: what *allocate* returned, and the placement
    :raises ModelServerNoResourcesException: if no server accepted the model and some were only
            full (no free slot): the allocation may succeed later
    :raises RuntimeError: if no compatible server was found or all failed otherwise; the last
            error is chained
    """
    loads = loads or {}
    ranking = ', '.join(f'{c.describe()} ({loads.get(c.nsName) or "load unknown"}' + (f', {c.score} preferred tag(s)' if req.optional else '') + ')' for c in ranked)
    log.info(f'Model {req.model} ({req.describe()}): compatible model servers, best first: {ranking or "none"}')
    if not ranked:
        raise RuntimeError(f'No model server compatible with model {req.model} is registered or reachable ({req.describe()}).')
    placement = Placement(model=req.model, nsName='', profile=req.profile)
    lastError: Optional[BaseException] = None
    full = False
    for c in ranked:
        try:
            ret = allocate(c)
        except Exception as e:
            lastError = e
            if isNoResourcesError(e):
                full = True
                reason = 'no free slot'
            elif isCannotRunError(e):
                # not retryable on this server: the model is unknown or not runnable there
                reason = f'cannot run the model: {e}'
            else:
                reason = f'{type(e).__name__}: {e}'
            placement.skipped.append((c.nsName, reason))
            log.warning(f'Model {req.model}: model server {c.nsName} did not accept the model ({reason}); trying the next one')
            continue
        placement.nsName = c.nsName
        log.info(f'Model {req.model} allocated on model server {c.nsName}' + (f' (after skipping {", ".join(n for n, _ in placement.skipped)})' if placement.skipped else ''))
        return ret, placement
    msg = f'No compatible model server accepted model {req.model}: ' + '; '.join(f'{n}: {r}' for n, r in placement.skipped)
    log.error(msg)
    if full:
        raise modelserverbase.ModelServerNoResourcesException(msg) from lastError
    raise RuntimeError(msg) from lastError
