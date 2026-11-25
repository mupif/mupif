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
Execution servers: generic compute nodes running any published model on demand.

A :class:`mupif.ModelServer` serves one model, which must be installed on its host beforehand. An
:class:`ExecutionServer` serves **any model package of a registry** (see :mod:`mupif.modelpackage`):
a client asks for a job of a model given by its ID (and optionally version), and the server

1. resolves the package in its registry (e.g. mupifDB, :class:`mupif.mupifdbclient.MupifDBRegistry`);
2. checks it can run it: the package's runtime (``pixi``, ``python``) is supported here and every
   *host capability* it requires is configured -- otherwise it refuses at once
   (:class:`~mupif.modelserverbase.ModelServerCannotRunException`), and the client tries another
   server;
3. gets the package from its cache, or -- on the first request (*on demand*) -- downloads it,
   verifies it against the digest recorded by the registry, extracts it and installs its
   environment (:mod:`mupif.packagecache`); this may take minutes and is not counted in the job
   start timeout;
4. starts the job like a model server does, but with the model's entry point imported by the job
   in the package's environment (:mod:`mupif.launcher`).

The client receives the usual ``(JOBMAN_OK, jobID, port)`` and talks to the job as to any remote
model. :meth:`ExecutionServer.getJobPackage` tells which package (ID, version, digest) a job runs,
which workflows record for provenance.

**Host capabilities** are what a host offers beyond packages: e.g. a licensed solver installed on it
which cannot be redistributed in a package. They are configured per server::

    hostCapabilities={'abaqus': {'Version': '2024', 'Path': ['/opt/abaqus/bin'],
                                 'Env': {'LM_LICENSE_FILE': '27000@licsrv'}}}

A package lists the names it needs (``RequiresHost``); its jobs get the ``Env`` and ``Path`` of
exactly those capabilities.

**Registration**: execution servers are registered in the nameserver with ``type:executionserver``
(see :func:`mupif.pyroutil.executionServerTags`), not ``type:jobmanager``, so that clients which do
not know them never ask them for a job without a model ID.

**Security**: a client can only name a model ID; the code run is always a package of the registry,
verified by its digest. Who may publish to the registry is therefore who may run code on execution
servers (in mupifDB: administrators). Pyro has no authentication: the VPN is the boundary.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Iterable, Mapping, Optional

import pydantic
import Pyro5.api

from . import modelserverbase
from . import pyroutil
from .launcher import Launcher, LocalPythonLauncher, PixiLauncher
from .modelpackage import ModelPackageManifest, ModelPackageNotFound, ModelRegistry, PackageRef
from .modelserver import ModelServer
from .packagecache import PackageBuildError, PackageCache

log = logging.getLogger(__name__)


class HostCapability(pydantic.BaseModel):
    """Something the host offers to models which need it (see the module documentation)."""
    model_config = pydantic.ConfigDict(extra='forbid')
    #: version of the tool, for information (logs, :meth:`ExecutionServer.getCapabilities`)
    Version: str = ''
    #: environment variables set for jobs of models requiring the capability
    Env: dict[str, str] = {}
    #: directories prepended to ``PATH`` of those jobs
    Path: list[str] = []


@Pyro5.api.expose
class ExecutionServer(ModelServer):
    """
    A model server running any model package of a registry on demand (see the module documentation).

    :param ns: nameserver proxy
    :param appName: base name of the server in the nameserver
    :param registry: where model packages are found
    :param cacheDir: directory of the package cache (packages and their environments; may be large)
    :param hostCapabilities: name -> :class:`HostCapability` (or a dict of its fields)
    :param runtimes: package runtimes run here; default: ``pixi`` if pixi is found, plus ``python``
                     if *allowPythonRuntime*
    :param allowPythonRuntime: run packages of runtime ``python`` (in the server's own environment;
                               their dependencies are not isolated from the server's)
    :param pixi: pixi executable (default: see :meth:`mupif.launcher.PixiLauncher.findPixi`)
    :param maxCacheBytes: size of the cache above which least recently used packages are removed
    :param failureTimeout: seconds a package which could not be prepared is not tried again
    :param workDir: see :class:`mupif.ModelServer`
    :param maxJobs: see :class:`mupif.ModelServer`
    :param instance: see :class:`mupif.ModelServer`
    """

    def __init__(
            self,
            *,
            ns,
            appName: str,
            registry: ModelRegistry,
            cacheDir,
            hostCapabilities: Optional[Mapping[str, object]] = None,
            runtimes: Optional[Iterable[str]] = None,
            allowPythonRuntime: bool = False,
            pixi: Optional[str] = None,
            maxCacheBytes: Optional[int] = None,
            failureTimeout: float = 600.,
            workDir=None,
            maxJobs: int = 1,
            instance=None,
            server=None,
            daemon=None,
    ):
        super().__init__(ns=ns, appName=appName, appClass=None, server=server, workDir=workDir, maxJobs=maxJobs, daemon=daemon, instance=instance)
        self.registry = registry
        self.cache = PackageCache(cacheDir, maxBytes=maxCacheBytes, failureTimeout=failureTimeout)
        self.hostCapabilities: dict[str, HostCapability] = {name: HostCapability.model_validate(c) for name, c in (hostCapabilities or {}).items()}
        self.pixi = pixi if pixi is not None else PixiLauncher.findPixi()
        if self.pixi is not None and not (os.path.isfile(self.pixi) and os.access(self.pixi, os.X_OK)):
            log.warning(f'{self.pixi} is not an executable file: runtime pixi not available')
            self.pixi = None
        if runtimes is None:
            runtimes = (['pixi'] if self.pixi else []) + (['python'] if allowPythonRuntime else [])
        self.runtimes: frozenset[str] = frozenset(runtimes)
        if 'pixi' in self.runtimes and not self.pixi:
            raise ValueError('Runtime pixi requested, but pixi was not found (pass pixi=..., set PIXI_EXE or put it into PATH)')
        # prepared launchers, by package digest: preparing a launcher (e.g. reading the pixi
        # activation) is done once per server process
        self._launchers: dict[str, Launcher] = {}
        self._launchersLock = threading.Lock()
        #: job ID -> package the job runs (kept for finished jobs, too)
        self._jobPackages: dict[str, PackageRef] = {}
        log.info(f'Execution server {appName}: registry {registry.describe()}, cache {cacheDir}, runtimes {sorted(self.runtimes) or "none"}, host capabilities {sorted(self.hostCapabilities) or "none"}')
        if not self.runtimes:
            log.warning(f'Execution server {appName} supports no package runtime: it will refuse every model (is pixi installed?)')

    def runServer(self):
        return pyroutil.runExecutionServer(ns=self.ns, server=self)

    def getApplicationSignature(self):
        return 'Mupif.ExecutionServer'

    def getCapabilities(self) -> dict:
        """
        Return what the server offers: runtimes and host capabilities (name -> version).

        For monitoring and diagnostics; clients find servers by their nameserver tags.
        """
        return {'runtimes': sorted(self.runtimes), 'hostCapabilities': {n: c.Version for n, c in self.hostCapabilities.items()}}

    def _checkRunnable(self, manifest: ModelPackageManifest) -> None:
        """Raise :class:`ModelServerCannotRunException` if the package cannot run on this server."""
        if manifest.Runtime.Type not in self.runtimes:
            raise modelserverbase.ModelServerCannotRunException(f'{self.getNSName()}: cannot run {manifest.key()}: runtime {manifest.Runtime.Type!r} not supported here (supported: {sorted(self.runtimes)})')
        missing = [c for c in manifest.RequiresHost if c not in self.hostCapabilities]
        if missing:
            raise modelserverbase.ModelServerCannotRunException(f'{self.getNSName()}: cannot run {manifest.key()}: host capabilities {missing} not available here (available: {sorted(self.hostCapabilities)})')

    def _launcherFor(self, ref: PackageRef, packageDir: Path) -> Launcher:
        """Return the launcher of a package (created once per digest), with the env of the capabilities it requires."""
        with self._launchersLock:
            launcher = self._launchers.get(ref.digest)
            if launcher is not None:
                return launcher
            manifest = ref.manifest
            extraEnv: dict[str, str] = {}
            extraPath: list[str] = []
            # only the capabilities the model asks for (least privilege: e.g. a licence of one
            # solver is not handed to every model)
            for name in manifest.RequiresHost:
                cap = self.hostCapabilities[name]
                extraEnv.update(cap.Env)
                extraPath.extend(cap.Path)
            if manifest.Runtime.Type == 'pixi':
                launcher = PixiLauncher(packageDir, environment=manifest.Runtime.Environment, pixi=self.pixi, extraEnv=extraEnv, extraPath=extraPath)
            elif manifest.Runtime.Type == 'python':
                launcher = LocalPythonLauncher(pythonPath=[str(packageDir)], extraEnv=extraEnv, extraPath=extraPath)
            else:  # excluded by _checkRunnable
                raise modelserverbase.ModelServerCannotRunException(f'Unsupported runtime {manifest.Runtime.Type!r}')
            self._launchers[ref.digest] = launcher
            return launcher

    def _getPackage(self, ref: PackageRef) -> Path:
        """Return the directory of the prepared package (getting it first, on demand)."""
        def prepare(packageDir: Path, manifest: ModelPackageManifest):
            self._launcherFor(ref, packageDir).prepare()
        try:
            return self.cache.get(ref, self.registry.download, prepare)
        except PackageBuildError as e:
            raise modelserverbase.ModelServerCannotRunException(f'{self.getNSName()}: {e}') from e

    def allocateJob(self, user, *, remoteLogUri=None, ticket=None, modelID: Optional[str] = None, modelVersion: Optional[str] = None):
        """
        Allocate a job running the model *modelID* (see the module documentation).

        :param user: who asks (a label)
        :param remoteLogUri: see :meth:`mupif.ModelServer.allocateJob`
        :param ticket: see :meth:`mupif.ModelServer.allocateJob`
        :param modelID: ID of the model package
        :param modelVersion: its version; None: the latest one
        :return: ``(JOBMAN_OK, jobID, port)``
        :raises ModelServerNoResourcesException: no free job slot (checked first, before the package
                is got: a full server does not prepare packages for jobs it cannot run)
        :raises ModelServerCannotRunException: no model ID given, the model is not in the registry,
                or cannot run here (runtime, host capability, package cannot be prepared)
        """
        if not modelID:
            raise modelserverbase.ModelServerCannotRunException(f'{self.getNSName()} is an execution server: the model ID must be given (allocateJob(..., modelID=...))')
        if ticket is None and self.getNumberOfFreeJobs() <= 0:
            raise modelserverbase.ModelServerNoResourcesException(f'{self.getNSName()}: no free job slot')
        try:
            ref = self.registry.resolve(modelID, modelVersion)
        except ModelPackageNotFound as e:
            raise modelserverbase.ModelServerCannotRunException(f'{self.getNSName()}: {e}') from e
        self._checkRunnable(ref.manifest)
        packageDir = self._getPackage(ref)
        spec = ModelServer.JobSpec(entrypoint=ref.manifest.Entrypoint, launcher=self._launcherFor(ref, packageDir))
        ret = self._allocateJob(user, remoteLogUri=remoteLogUri, ticket=ticket, spec=spec)
        jobID = ret[1]
        self._jobPackages[jobID] = ref
        log.info(f'Job {jobID} runs model package {ref.manifest.key()} ({ref.digest})')
        self._prune()
        return ret

    def getJobPackage(self, jobID: str) -> Optional[dict]:
        """
        Return the package a job runs: ``{ID, Version, Digest}``; None for an unknown job.

        Workflows record it for every model allocated on an execution server.
        """
        ref = self._jobPackages.get(jobID)
        return ref.describe() if ref is not None else None

    def _prune(self) -> None:
        """Shrink the cache, keeping the packages of running jobs; never raises."""
        try:
            self._updateActiveJobs()
            with self.lock:
                active = {self._jobPackages[j].digest for j in self.activeJobs if j in self._jobPackages}
            self.cache.prune(keep=active)
        except Exception:
            log.exception('Pruning the package cache failed')
