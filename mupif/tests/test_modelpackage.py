"""Tests of :mod:`mupif.modelpackage`: manifest, archives, digests, safe extraction, directory registry."""

import io
import os
import stat
import zipfile

import pytest

from mupif import modelpackage as mpk


MANIFEST = '''
ID = "{id}"
Version = "{version}"
Entrypoint = "mymodel.model:MyModel"
Description = "test"
RequiresHost = {requires}

[Runtime]
Type = "python"
'''


def makePackage(directory, id='my-model', version='1.0', requires='[]', code='VALUE = 1\n'):
    """Create a package directory and return its path."""
    os.makedirs(directory / 'mymodel', exist_ok=True)
    (directory / mpk.MANIFEST_NAME).write_text(MANIFEST.format(id=id, version=version, requires=requires))
    (directory / 'mymodel' / '__init__.py').write_text('')
    (directory / 'mymodel' / 'model.py').write_text(code)
    return directory


def test_manifest_valid_and_invalid():
    m = mpk.ModelPackageManifest.fromToml(MANIFEST.format(id='a.b-c', version='2.0+cvut', requires='["abaqus"]'))
    assert (m.ID, m.Version, m.Entrypoint, m.Runtime.Type, m.Runtime.Environment, m.RequiresHost) == ('a.b-c', '2.0+cvut', 'mymodel.model:MyModel', 'python', 'default', ['abaqus'])
    assert m.key() == 'a.b-c@2.0+cvut'
    # characters which would break nameserver tags (ModelID:<id>@<version>) or URLs
    for id in ('a@b', 'a:b', 'a/b', '', '.hidden'):
        with pytest.raises(mpk.ModelPackageError):
            mpk.ModelPackageManifest.fromToml(MANIFEST.format(id=id, version='1', requires='[]'))
    with pytest.raises(mpk.ModelPackageError):
        mpk.ModelPackageManifest.fromToml(MANIFEST.format(id='a', version='1', requires='[]').replace('mymodel.model:MyModel', 'mymodel.model'))
    with pytest.raises(mpk.ModelPackageError):  # unknown key (typo) is not silently ignored
        mpk.ModelPackageManifest.fromToml(MANIFEST.format(id='a', version='1', requires='[]') + 'Requires = []\n')
    with pytest.raises(mpk.ModelPackageError):
        mpk.ModelPackageManifest.fromToml('not = [toml')


def test_version_key_orders_latest_last():
    versions = ['1.10', '1.2', '1.9.1', '1.2.rc1', '1.2.0', '2']
    assert sorted(versions, key=mpk.versionKey) == ['1.2', '1.2.rc1', '1.2.0', '1.9.1', '1.10', '2']


def test_archive_is_deterministic_and_excludes_environments(tmp_path):
    pkg = makePackage(tmp_path / 'pkg')
    (pkg / '.pixi' / 'envs').mkdir(parents=True)
    (pkg / '.pixi' / 'envs' / 'big').write_text('x')
    (pkg / 'mymodel' / '__pycache__').mkdir()
    (pkg / 'mymodel' / '__pycache__' / 'model.cpython-312.pyc').write_bytes(b'x')
    a1 = mpk.buildArchive(pkg)
    # touching files (new mtimes) does not change the archive
    os.utime(pkg / 'mymodel' / 'model.py', (1, 1))
    a2 = mpk.buildArchive(pkg)
    assert a1 == a2 and mpk.digest(a1) == mpk.digest(a2)
    assert mpk.digest(a1).startswith('sha256:') and len(mpk.digest(a1)) == 7 + 64
    names = zipfile.ZipFile(io.BytesIO(a1)).namelist()
    assert names == sorted(['mupif-model.toml', 'mymodel/__init__.py', 'mymodel/model.py'])
    # different content, different digest
    (pkg / 'mymodel' / 'model.py').write_text('VALUE = 2\n')
    assert mpk.digest(mpk.buildArchive(pkg)) != mpk.digest(a1)


def test_archive_needs_manifest_and_refuses_links(tmp_path):
    (tmp_path / 'empty').mkdir()
    with pytest.raises(mpk.ModelPackageError):
        mpk.buildArchive(tmp_path / 'empty')
    pkg = makePackage(tmp_path / 'pkg')
    os.symlink('/etc/passwd', pkg / 'link')
    with pytest.raises(mpk.ModelPackageError):
        mpk.buildArchive(pkg)


def test_safe_extract_round_trip_keeps_exec_bit(tmp_path):
    pkg = makePackage(tmp_path / 'pkg')
    (pkg / 'run.sh').write_text('#!/bin/sh\n')
    os.chmod(pkg / 'run.sh', 0o755)
    dest = tmp_path / 'out'
    dest.mkdir()
    m = mpk.safeExtract(mpk.buildArchive(pkg), dest)
    assert m.ID == 'my-model'
    assert (dest / 'mymodel' / 'model.py').read_text() == 'VALUE = 1\n'
    assert os.access(dest / 'run.sh', os.X_OK)


def zipWith(entries, manifest=True):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        if manifest:
            zf.writestr(mpk.MANIFEST_NAME, MANIFEST.format(id='m', version='1', requires='[]'))
        for info, content in entries:
            zf.writestr(info, content)
    return buf.getvalue()


@pytest.mark.parametrize('name', ['../evil.py', '/abs/evil.py', 'a/../../evil.py', 'C:/evil.py'])
def test_safe_extract_refuses_unsafe_paths(tmp_path, name):
    with pytest.raises(mpk.ModelPackageError):
        mpk.safeExtract(zipWith([(name, 'x')]), tmp_path)
    # nothing extracted, not even the valid members
    assert list(tmp_path.iterdir()) == []


def test_safe_extract_refuses_links_and_missing_manifest(tmp_path):
    link = zipfile.ZipInfo('link')
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(mpk.ModelPackageError):
        mpk.safeExtract(zipWith([(link, '/etc/passwd')]), tmp_path)
    with pytest.raises(mpk.ModelPackageError):
        mpk.safeExtract(zipWith([('a.py', 'x')], manifest=False), tmp_path)
    with pytest.raises(mpk.ModelPackageError):
        mpk.safeExtract(b'not a zip', tmp_path)


def test_directory_registry_resolves_latest_and_pinned(tmp_path):
    reg = tmp_path / 'reg'
    makePackage(reg / 'a1', version='1.9')
    makePackage(reg / 'a2', version='1.10')
    # an archive file is a package too
    other = makePackage(tmp_path / 'other', id='other', version='3')
    (reg / 'other.zip').write_bytes(mpk.buildArchive(other))
    # an invalid package is skipped, not fatal
    (reg / 'broken').mkdir()
    (reg / 'broken' / mpk.MANIFEST_NAME).write_text('ID = "x"')
    r = mpk.DirectoryRegistry(reg)
    ref = r.resolve('my-model')
    assert ref.version == '1.10' and ref.location == str(reg / 'a2')
    assert r.resolve('my-model', '1.9').location == str(reg / 'a1')
    data = r.download(ref)
    assert mpk.digest(data) == ref.digest
    assert ref.describe() == {'ID': 'my-model', 'Version': '1.10', 'Digest': ref.digest}
    zref = r.resolve('other')
    assert r.download(zref) == (reg / 'other.zip').read_bytes() and zref.digest == mpk.digest(r.download(zref))
    for args in (('nope',), ('my-model', '7')):
        with pytest.raises(mpk.ModelPackageNotFound):
            r.resolve(*args)


def test_directory_registry_refuses_duplicates(tmp_path):
    makePackage(tmp_path / 'x', version='1')
    makePackage(tmp_path / 'y', version='1', code='VALUE = 2\n')
    with pytest.raises(mpk.ModelPackageError):
        mpk.DirectoryRegistry(tmp_path).resolve('my-model')


H = 'a' * 64


@pytest.mark.parametrize('runtime,ok', [
    (f'Type = "apptainer"\nImage = "docker://ghcr.io/mupif/oofem@sha256:{H}"', True),
    (f'Type = "apptainer"\nImage = "oras://ghcr.io/mupif/oofem@sha256:{H}"\nGpu = true\nPython = "/opt/conda/bin/python"', True),
    (f'Type = "apptainer"\nImage = "https://example.org/oofem.sif"\nImageDigest = "sha256:{H}"', True),
    (f'Type = "apptainer"\nImage = "file:///shared/images/oofem.sif"\nImageDigest = "sha256:{H}"', True),
    # registry images must be pinned by digest (a tag can be moved)
    ('Type = "apptainer"\nImage = "docker://ghcr.io/mupif/oofem:1.2"', False),
    # SIF files need their digest; registry images must not have one (pinned already)
    ('Type = "apptainer"\nImage = "https://example.org/oofem.sif"', False),
    (f'Type = "apptainer"\nImage = "file:///x.sif"\nImageDigest = "md5:{H}"', False),
    (f'Type = "apptainer"\nImage = "docker://ghcr.io/x@sha256:{H}"\nImageDigest = "sha256:{H}"', False),
    # other schemes: library://, relative paths, plain http
    ('Type = "apptainer"\nImage = "library://sylabs/x"', False),
    (f'Type = "apptainer"\nImage = "http://example.org/x.sif"\nImageDigest = "sha256:{H}"', False),
    (f'Type = "apptainer"\nImage = "file://x.sif"\nImageDigest = "sha256:{H}"', False),
    ('Type = "apptainer"', False),
    # image fields only with apptainer
    (f'Type = "pixi"\nImage = "docker://x@sha256:{H}"', False),
    ('Type = "python"\nGpu = true', False),
    # the interpreter is a path, not a command line
    (f'Type = "apptainer"\nImage = "docker://x/y@sha256:{H}"\nPython = "python3 -c evil"', False),
])
def test_manifest_apptainer_runtime(runtime, ok):
    text = MANIFEST.format(id='m', version='1', requires='[]').replace('Type = "python"', runtime)
    if ok:
        assert mpk.ModelPackageManifest.fromToml(text).Runtime.Type == 'apptainer'
    else:
        with pytest.raises(mpk.ModelPackageError):
            mpk.ModelPackageManifest.fromToml(text)


def test_archive_excludes_apptainer_images(tmp_path):
    pkg = makePackage(tmp_path / 'pkg')
    (pkg / '.apptainer').mkdir()
    (pkg / '.apptainer' / 'image.sif').write_bytes(b'x' * 100)
    assert '.apptainer/image.sif' not in zipfile.ZipFile(io.BytesIO(mpk.buildArchive(pkg))).namelist()
