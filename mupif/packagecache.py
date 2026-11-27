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
Cache of model packages on an execution server: downloaded, verified, extracted and prepared once.

An execution server (:mod:`mupif.executionserver`) gets a model package on the first request for it
(*on demand*): the archive is downloaded from the registry, verified against the digest the registry
recorded, extracted, and its environment is prepared (e.g. ``pixi install``). All that may take
minutes; later requests find the package ready in the cache and start at once.

Layout of the cache directory::

    <cache>/<sha256 hex>/package/   the extracted package; its environment is installed inside
                                    (pixi: package/.pixi/), which is why a package is never moved
                                    once prepared (environments contain absolute paths)
    <cache>/<sha256 hex>/ready      written when the package is prepared; its mtime is the last use
    <cache>/<sha256 hex>.lock       lock file (several server processes may share the cache)

A package is identified by its **digest**: published content never changes, so a ready entry never
becomes stale, and two versions with the same content share one entry.

**Concurrency**: a lock per digest (a thread lock and, where available, an ``flock`` on the lock
file) makes concurrent requests for the same package download and prepare it once; requests for
other packages are not blocked.

**Failures** to download, verify or prepare a package are remembered for
:attr:`PackageCache.failureTimeout` seconds: requests meanwhile fail at once, with the original
error, instead of every request repeating a long failing build (the client then tries another
server). An incomplete entry left by a failure or a crash is removed and built again.

**Pruning**: :meth:`PackageCache.prune` removes the least recently used ready entries while the
cache is larger than its limit, never the packages given as in use (those of running jobs).
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Iterable, Optional, Union

from .modelpackage import ModelPackageError, ModelPackageManifest, PackageRef, digest as archiveDigest, safeExtract

try:
    import fcntl
except ImportError:  # Windows: no inter-process lock (one server process per cache directory)
    fcntl = None  # type: ignore[assignment]

log = logging.getLogger(__name__)


class PackageBuildError(ModelPackageError):
    """A package could not be downloaded, verified or prepared (possibly remembered from an earlier attempt)."""


def _hex(digest: str) -> str:
    """Return the hex part of ``sha256:<hex>``, the name of the cache entry; refuse anything else."""
    algo, sep, hexpart = digest.partition(':')
    if algo != 'sha256' or not sep or len(hexpart) != 64 or any(c not in '0123456789abcdef' for c in hexpart):
        raise ModelPackageError(f'Invalid package digest {digest!r} (expected sha256:<64 hex digits>)')
    return hexpart


def _dirSize(path: Path) -> int:
    """Return the total size of the files below *path* (links not followed)."""
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


class PackageCache:
    """
    Packages downloaded, verified, extracted and prepared once (see the module documentation).

    :param directory: cache directory (created if needed)
    :param maxBytes: size above which :meth:`prune` removes least recently used entries; None: no limit
    :param failureTimeout: seconds a failure is remembered
    """

    def __init__(self, directory: Union[str, os.PathLike], *, maxBytes: Optional[int] = None, failureTimeout: float = 600.):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.maxBytes = maxBytes
        self.failureTimeout = failureTimeout
        self._lock = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}
        #: digest -> (time.monotonic() of the failure, message)
        self._failures: dict[str, tuple[float, str]] = {}

    def packageDir(self, ref: PackageRef) -> Path:
        """Return the directory the package of *ref* is (or will be) extracted to."""
        return self.directory / _hex(ref.digest) / 'package'

    def isReady(self, ref: PackageRef) -> bool:
        """Tell whether the package of *ref* is ready (a request would start without building)."""
        return (self.directory / _hex(ref.digest) / 'ready').exists()

    def readyPackages(self) -> dict[str, str]:
        """
        Return the ready packages in the cache: digest -> ``<ID>@<Version>``.

        Read from the ``ready`` files, so it includes packages prepared by earlier runs of the
        server (an execution server advertises them when it starts).
        """
        ret = {}
        for entry in self.directory.iterdir():
            ready = entry / 'ready'
            if entry.is_dir() and not entry.name.startswith('.') and ready.exists():
                try:
                    key, dig = ready.read_text().split()
                except (OSError, ValueError):
                    continue
                if dig == 'sha256:' + entry.name:
                    ret[dig] = key
        return ret

    @contextlib.contextmanager
    def _locked(self, hexd: str):
        """Hold the lock of one package: the thread lock, then the lock file (other processes)."""
        with self._lock:
            lock = self._locks.setdefault(hexd, threading.Lock())
        with lock:
            if fcntl is None:
                yield
                return
            with open(self.directory / f'{hexd}.lock', 'a') as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)

    def get(self, ref: PackageRef, download: Callable[[PackageRef], bytes], prepare: Callable[[Path, ModelPackageManifest], None]) -> Path:
        """
        Return the directory of the ready package of *ref*, getting and preparing it first if needed.

        :param ref: the package (from :meth:`mupif.modelpackage.ModelRegistry.resolve`)
        :param download: returns the archive of the package (e.g. the registry's ``download``)
        :param prepare: prepares the extracted package (installs its environment); called with the
                        package directory, which is its final location, and the manifest
        :return: the package directory
        :raises PackageBuildError: if the package cannot be downloaded, its archive does not match
                 the digest, or preparing it fails -- now or within :attr:`failureTimeout` before
        """
        hexd = _hex(ref.digest)
        with self._locked(hexd):
            failed = self._failures.get(ref.digest)
            if failed is not None:
                if time.monotonic() - failed[0] < self.failureTimeout:
                    raise PackageBuildError(f'{ref.manifest.key()} failed recently on this server, not retried before {self.failureTimeout:g} s pass: {failed[1]}')
                del self._failures[ref.digest]
            entry = self.directory / hexd
            ready = entry / 'ready'
            if ready.exists():
                os.utime(ready)  # last use, for pruning
                return entry / 'package'
            try:
                return self._build(ref, entry, download, prepare)
            except Exception as e:
                msg = f'{type(e).__name__}: {e}'
                self._failures[ref.digest] = (time.monotonic(), msg)
                log.error(f'Model package {ref.manifest.key()} ({ref.digest}) could not be prepared: {msg}')
                if isinstance(e, PackageBuildError):
                    raise
                raise PackageBuildError(f'{ref.manifest.key()}: {msg}') from e

    def _build(self, ref: PackageRef, entry: Path, download, prepare) -> Path:
        """Download, verify, extract and prepare a package into *entry* (lock held)."""
        if entry.exists():
            # left over by a failed or interrupted build: start afresh
            log.warning(f'Removing incomplete cache entry {entry}')
            shutil.rmtree(entry)
        t0 = time.monotonic()
        data = download(ref)
        got = archiveDigest(data)
        if got != ref.digest:
            raise PackageBuildError(f'{ref.manifest.key()}: downloaded archive has digest {got}, the registry recorded {ref.digest}; refusing it')
        # extract under a temporary name and move into place, then prepare there (never moved after
        # preparing: installed environments contain absolute paths)
        tmp = self.directory / f'.tmp-{_hex(ref.digest)}-{uuid.uuid4().hex}'
        try:
            (tmp / 'package').mkdir(parents=True)
            manifest = safeExtract(data, tmp / 'package')
            if manifest.key() != ref.manifest.key():
                raise PackageBuildError(f'Archive contains package {manifest.key()}, expected {ref.manifest.key()}')
            os.rename(tmp, entry)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        log.info(f'Model package {ref.manifest.key()} ({len(data)} bytes) downloaded and extracted to {entry} in {time.monotonic()-t0:.1f} s; preparing')
        t1 = time.monotonic()
        try:
            prepare(entry / 'package', manifest)
        except Exception:
            shutil.rmtree(entry, ignore_errors=True)
            raise
        (entry / 'ready').write_text(f'{ref.manifest.key()} {ref.digest}\n')
        log.info(f'Model package {ref.manifest.key()} prepared in {time.monotonic()-t1:.1f} s')
        return entry / 'package'

    def prune(self, keep: Iterable[str] = ()) -> list[str]:
        """
        Remove least recently used ready packages while the cache is larger than :attr:`maxBytes`.

        :param keep: digests never removed (packages of running jobs)
        :return: digests of the removed packages
        """
        if self.maxBytes is None:
            return []
        keepHex = {_hex(d) for d in keep}
        entries = []
        for entry in self.directory.iterdir():
            ready = entry / 'ready'
            if entry.is_dir() and not entry.name.startswith('.') and ready.exists():
                entries.append((ready.stat().st_mtime, _dirSize(entry), entry))
        total = sum(size for _, size, _ in entries)
        removed = []
        for _, size, entry in sorted(entries, key=lambda e: e[0]):
            if total <= self.maxBytes:
                break
            if entry.name in keepHex:
                continue
            with self._locked(entry.name):
                shutil.rmtree(entry, ignore_errors=True)
            total -= size
            removed.append('sha256:' + entry.name)
            log.info(f'Model package sha256:{entry.name} removed from the cache (least recently used)')
        return removed
