"""Tests of :mod:`mupif.packagecache`: on-demand download, verification, preparation, failures, pruning."""

import os
import threading
import time

import pytest

from mupif import modelpackage as mpk
from mupif.packagecache import PackageBuildError, PackageCache

from .test_modelpackage import makePackage


@pytest.fixture
def registry(tmp_path):
    makePackage(tmp_path / 'reg' / 'a', version='1')
    makePackage(tmp_path / 'reg' / 'b', id='other', version='1', code='VALUE = 2\n')
    return mpk.DirectoryRegistry(tmp_path / 'reg')


class Counting:
    """download/prepare callables counting their calls; prepare may fail or be slow."""
    def __init__(self, registry, fail=False, delay=0.):
        self.registry, self.fail, self.delay = registry, fail, delay
        self.downloads = self.prepares = 0

    def download(self, ref):
        self.downloads += 1
        return self.registry.download(ref)

    def prepare(self, path, manifest):
        self.prepares += 1
        time.sleep(self.delay)
        assert (path / 'mymodel' / 'model.py').exists() and manifest.ID in ('my-model', 'other')
        (path / '.pixi').mkdir()  # an "environment" installed inside the package
        if self.fail:
            raise RuntimeError('pixi install failed')


def test_get_once_then_ready(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache')
    ref = registry.resolve('my-model')
    c = Counting(registry)
    assert not cache.isReady(ref)
    p1 = cache.get(ref, c.download, c.prepare)
    p2 = cache.get(ref, c.download, c.prepare)
    assert p1 == p2 == cache.packageDir(ref) and (p1 / '.pixi').is_dir()
    assert (c.downloads, c.prepares) == (1, 1)
    assert cache.isReady(ref)
    # a new cache object on the same directory (server restarted) finds it ready
    assert PackageCache(tmp_path / 'cache').get(ref, c.download, c.prepare) == p1 and c.downloads == 1


def test_concurrent_requests_build_once(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache')
    ref = registry.resolve('my-model')
    c = Counting(registry, delay=0.3)
    results = []
    threads = [threading.Thread(target=lambda: results.append(cache.get(ref, c.download, c.prepare))) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(set(results)) == 1 and (c.downloads, c.prepares) == (1, 1)


def test_digest_mismatch_refused(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache')
    ref = registry.resolve('my-model')
    tampered = lambda ref: registry.download(registry.resolve('other'))
    with pytest.raises(PackageBuildError, match='digest'):
        cache.get(ref, tampered, Counting(registry).prepare)
    assert not cache.isReady(ref) and not cache.packageDir(ref).exists()


def test_failure_remembered_then_retried(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache', failureTimeout=0.3)
    ref = registry.resolve('my-model')
    bad = Counting(registry, fail=True)
    with pytest.raises(PackageBuildError, match='pixi install failed'):
        cache.get(ref, bad.download, bad.prepare)
    # the incomplete entry is gone
    assert not cache.packageDir(ref).exists()
    # within the timeout: refused at once, nothing attempted
    with pytest.raises(PackageBuildError, match='failed recently'):
        cache.get(ref, bad.download, bad.prepare)
    assert bad.prepares == 1
    # other packages are not affected
    good = Counting(registry)
    cache.get(registry.resolve('other'), good.download, good.prepare)
    time.sleep(0.35)
    assert cache.get(ref, good.download, good.prepare).is_dir()


def test_incomplete_entry_rebuilt(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache')
    ref = registry.resolve('my-model')
    # a crash after extraction, before "ready"
    cache.packageDir(ref).mkdir(parents=True)
    (cache.packageDir(ref) / 'junk').write_text('x')
    c = Counting(registry)
    p = cache.get(ref, c.download, c.prepare)
    assert c.prepares == 1 and not (p / 'junk').exists()


def test_invalid_digest_refused(tmp_path, registry):
    ref = registry.resolve('my-model')
    import dataclasses
    for bad in ('md5:abc', 'sha256:../../etc', 'sha256:' + 'g' * 64):
        with pytest.raises(mpk.ModelPackageError):
            PackageCache(tmp_path / 'cache').packageDir(dataclasses.replace(ref, digest=bad))


def test_prune_lru_keeps_in_use(tmp_path, registry):
    cache = PackageCache(tmp_path / 'cache', maxBytes=0)
    c = Counting(registry)
    a, b = registry.resolve('my-model'), registry.resolve('other')
    cache.get(a, c.download, c.prepare)
    cache.get(b, c.download, c.prepare)
    # both in use (packages of running jobs): nothing removed, although over the limit
    assert cache.prune(keep=[a.digest, b.digest]) == []
    os.utime(cache.directory / a.digest[7:] / 'ready', (1, 1))  # a least recently used
    assert cache.prune(keep=[b.digest]) == [a.digest]
    assert not cache.isReady(a) and cache.isReady(b)
    assert PackageCache(tmp_path / 'cache2').prune() == []  # no limit: never prunes
