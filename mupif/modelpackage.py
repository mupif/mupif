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
Model packages: a model with everything needed to run it, published to a registry.

An execution server (:mod:`mupif.executionserver`) runs any model *package* from a registry on
demand. A package is a directory (or a zip archive of it) containing:

* ``mupif-model.toml`` -- the *manifest* (:class:`ModelPackageManifest`), e.g.::

      ID = "oofem-thermal"
      Version = "1.2"
      Entrypoint = "oofemthermal.model:ThermalModel"   # the mupif.Model subclass
      Description = "Stationary heat transfer, OOFEM"
      RequiresHost = []                                # host capabilities, e.g. ["abaqus"]

      [Runtime]
      Type = "pixi"            # environment of pixi.toml/pixi.lock of the package; or "python",
                               # or "apptainer" (a container image, see RuntimeSpec)
      Environment = "default"  # pixi environment name

* the model code, importable from the package directory (``oofemthermal/model.py`` above);
* for ``Runtime.Type = "pixi"``: ``pixi.toml`` and ``pixi.lock``, the environment of the model
  (its solver, Python, mupif, ...); the lock file makes it reproducible.

``Runtime.Type = "python"`` runs the model in the execution server's own environment, with the
package directory added to ``PYTHONPATH``: for pure-Python models whose dependencies the server has
anyway, and for tests.

A package version is **immutable**: its archive is identified by a **digest** (``sha256:<hex>``)
computed from a deterministic archive of the package (:func:`buildArchive`), so that the same
content always gives the same digest. The registry records it when the package is published;
an execution server verifies every downloaded archive against it, and the workflow execution records
the digest of every model it ran.

**Registries** (:class:`ModelRegistry`) resolve a model ID (and optionally a version) to a
:class:`PackageRef` and download its archive:

* :class:`DirectoryRegistry` -- packages (directories or zip archives) in a local directory, for
  tests and for hosts without a database;
* :class:`mupif.mupifdbclient.MupifDBRegistry` -- packages published to mupifDB.
"""

from __future__ import annotations

import abc
import dataclasses
import hashlib
import io
import logging
import os
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal, Optional, Union

import pydantic

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

log = logging.getLogger(__name__)

#: file name of the manifest, at the top level of a package
MANIFEST_NAME = 'mupif-model.toml'

#: directories and files never put into a package archive: environments installed into the package
#: directory, caches, version control
ARCHIVE_EXCLUDE_DIRS = frozenset({'.pixi', '.apptainer', '__pycache__', '.git', '.hg', '.svn', '.mypy_cache', '.pytest_cache'})
ARCHIVE_EXCLUDE_SUFFIXES = ('.pyc', '.pyo', '~')

#: model IDs and versions appear in nameserver tags (``ModelID:<id>@<version>``) and URLs
_ID_PATTERN = r'^[A-Za-z0-9][A-Za-z0-9._-]*$'
_VERSION_PATTERN = r'^[A-Za-z0-9][A-Za-z0-9.+_-]*$'
_ENTRYPOINT_PATTERN = r'^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_.]*$'


class ModelPackageError(Exception):
    """A model package is invalid, or cannot be found or used."""


class ModelPackageNotFound(ModelPackageError, LookupError):
    """The registry has no package of the requested model ID (and version)."""


#: image references pinned by digest: OCI registries (``docker://``, ``oras://``)
_PINNED_REF = re.compile(r'^(docker|oras)://[^@\s]+@sha256:[0-9a-f]{64}$')
#: SIF files given by location, verified against ``ImageDigest``
_SIF_URL = re.compile(r'^(https://|file:///)\S+$')
_SHA256 = re.compile(r'^sha256:[0-9a-f]{64}$')


class RuntimeSpec(pydantic.BaseModel):
    """
    How the environment of a model package is made (``[Runtime]`` of the manifest).

    * ``pixi`` -- the environment of ``pixi.toml``/``pixi.lock`` of the package (``Environment``);
    * ``python`` -- the execution server's own environment (package directory on ``PYTHONPATH``);
    * ``apptainer`` -- a container image (``Image``), run by Apptainer (Singularity); the package
      directory is mounted into the container at ``/mupif/package`` and put on ``PYTHONPATH``, so the
      model code may come with the package or be in the image. The image must contain Python and a
      mupif with execution servers. ``Image`` is immutable:

      - ``docker://<registry>/<name>@sha256:<hex>`` or ``oras://...@sha256:<hex>`` -- an OCI registry
        image pinned by digest (the registry content is verified by it);
      - ``https://.../<file>.sif`` or ``file:///<path>.sif`` (e.g. a shared file system of an HPC
        site) with ``ImageDigest = "sha256:<hex>"`` of the SIF file, verified by the server.

      ``Gpu = true`` gives the container the host's NVIDIA GPUs (``--nv``); ``Python`` is the
      interpreter in the image (default ``python3``).
    """
    model_config = pydantic.ConfigDict(extra='forbid')
    Type: Literal['pixi', 'python', 'apptainer']
    #: name of the pixi environment (``pixi`` only)
    Environment: str = 'default'
    #: the container image (``apptainer`` only); see the class documentation
    Image: str = ''
    #: ``sha256:<hex>`` of the SIF file, for ``https://`` and ``file:///`` images
    ImageDigest: str = ''
    #: give the container the host's NVIDIA GPUs (``apptainer`` only)
    Gpu: bool = False
    #: Python interpreter in the image (``apptainer`` only)
    Python: str = pydantic.Field('python3', pattern=r'^[A-Za-z0-9_./-]+$')

    @pydantic.model_validator(mode='after')
    def _imageRules(self):
        if self.Type != 'apptainer':
            if self.Image or self.ImageDigest or self.Gpu:
                raise ValueError(f'Image, ImageDigest and Gpu are for Type = "apptainer", not {self.Type!r}')
            return self
        if _PINNED_REF.match(self.Image):
            if self.ImageDigest:
                raise ValueError('ImageDigest is for https:// and file:/// images; a registry image is pinned by its @sha256 digest')
        elif _SIF_URL.match(self.Image):
            if not _SHA256.match(self.ImageDigest):
                raise ValueError(f'An https:// or file:/// image needs ImageDigest = "sha256:<64 hex digits>" of the SIF file (got {self.ImageDigest!r})')
        else:
            raise ValueError(f'Image must be docker://...@sha256:<hex>, oras://...@sha256:<hex> (pinned by digest), https://... or file:///... (got {self.Image!r})')
        return self


class ModelPackageManifest(pydantic.BaseModel):
    """The manifest of a model package (``mupif-model.toml``); see the module documentation."""
    model_config = pydantic.ConfigDict(extra='forbid')
    #: model ID: the ``ID`` in the model's metadata, by which workflows ask for the model (``ModelID``)
    ID: str = pydantic.Field(pattern=_ID_PATTERN)
    #: version of the package; never reused for different content
    Version: str = pydantic.Field(pattern=_VERSION_PATTERN)
    #: the model class, ``"module:Class"``, importable from the package directory
    Entrypoint: str = pydantic.Field(pattern=_ENTRYPOINT_PATTERN)
    #: environment of the model
    Runtime: RuntimeSpec
    #: host capabilities the model needs (names configured on execution servers, e.g. a licensed
    #: solver installed on the host); a server lacking any of them does not run the model
    RequiresHost: list[str] = []
    #: free-text description
    Description: str = ''

    @classmethod
    def fromToml(cls, text: Union[str, bytes]) -> 'ModelPackageManifest':
        """
        Parse and validate a manifest.

        :raises ModelPackageError: if it is not valid TOML or not a valid manifest
        """
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        try:
            return cls.model_validate(tomllib.loads(text))
        except (tomllib.TOMLDecodeError, pydantic.ValidationError) as e:
            raise ModelPackageError(f'Invalid {MANIFEST_NAME}: {e}') from e

    def key(self) -> str:
        """Return ``<ID>@<Version>``, the identity of the package (used in nameserver tags)."""
        return f'{self.ID}@{self.Version}'


@dataclasses.dataclass(frozen=True)
class PackageRef:
    """A model package found in a registry: its manifest, digest and where the registry keeps it."""
    manifest: ModelPackageManifest
    #: ``sha256:<hex>`` of the package archive
    digest: str
    #: registry-specific location (a path, a database file ID); not interpreted by the users
    location: str

    @property
    def ID(self) -> str:
        return self.manifest.ID

    @property
    def version(self) -> str:
        return self.manifest.Version

    def describe(self) -> dict[str, str]:
        """Return ``{ID, Version, Digest}``: what is recorded about the package a job ran."""
        return {'ID': self.manifest.ID, 'Version': self.manifest.Version, 'Digest': self.digest}


def versionKey(version: str) -> tuple:
    """
    Return a sort key of a version string, so that the *latest* version sorts last.

    Versions are compared part by part (split at ``.``, ``-``, ``+``, ``_``); numeric parts
    numerically, numeric parts after textual ones (``1.2.rc1`` < ``1.2.0``), so that ``1.10`` is
    later than ``1.9``. Good enough for the usual ``major.minor.patch`` schemes, without depending on
    ``packaging``. mupifDB uses the same function to resolve ``latest``.
    """
    key = []
    for part in re.split(r'[.\-+_]', version):
        if part.isdigit():
            key.append((1, int(part), ''))
        else:
            key.append((0, 0, part))
    return tuple(key)


def digest(data: bytes) -> str:
    """Return the digest of a package archive: ``sha256:<hex>``."""
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def _archiveMembers(directory: Path) -> list[tuple[str, Path]]:
    """Return ``(archive name, path)`` of the files of a package directory, sorted, without excluded ones."""
    members = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in ARCHIVE_EXCLUDE_DIRS)
        for f in sorted(files):
            if f.endswith(ARCHIVE_EXCLUDE_SUFFIXES):
                continue
            path = Path(root) / f
            if path.is_symlink():
                raise ModelPackageError(f'Symbolic links are not allowed in model packages: {path}')
            members.append((path.relative_to(directory).as_posix(), path))
    return sorted(members)


def buildArchive(directory: Union[str, os.PathLike]) -> bytes:
    """
    Pack a package directory into a zip archive, deterministically.

    The same files with the same content always give the same bytes (hence the same
    :func:`digest`): members are sorted, time stamps fixed, permissions normalized (0644, or 0755
    for executables). Installed environments (``.pixi``), caches and version control directories
    are left out (see :data:`ARCHIVE_EXCLUDE_DIRS`).

    :param directory: the package directory, with a valid manifest
    :return: the archive
    :raises ModelPackageError: if the manifest is missing or invalid, or the directory contains
                               symbolic links
    """
    directory = Path(directory)
    manifestPath = directory / MANIFEST_NAME
    if not manifestPath.is_file():
        raise ModelPackageError(f'{directory} is not a model package: {MANIFEST_NAME} not found')
    ModelPackageManifest.fromToml(manifestPath.read_bytes())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, path in _archiveMembers(directory):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if os.access(path, os.X_OK) else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            zf.writestr(info, path.read_bytes())
    return buf.getvalue()


def _checkMember(info: zipfile.ZipInfo) -> None:
    """
    Reject archive members which would be extracted outside the target directory, or are links.

    Same rule as mupifDB's workflow staging: no absolute paths, no ``..``, no drive letters.
    """
    name = info.filename
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or (path.parts and ':' in path.parts[0]):
        raise ModelPackageError(f'Unsafe path in model package archive: {name!r}')
    if stat.S_ISLNK(info.external_attr >> 16):
        raise ModelPackageError(f'Symbolic link in model package archive: {name!r}')


def readArchiveManifest(data: bytes) -> ModelPackageManifest:
    """
    Return the manifest of a package archive, without extracting anything.

    :raises ModelPackageError: if *data* is not a zip archive or has no valid manifest at its top level
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            try:
                return ModelPackageManifest.fromToml(zf.read(MANIFEST_NAME))
            except KeyError:
                raise ModelPackageError(f'Model package archive has no {MANIFEST_NAME} at its top level') from None
    except zipfile.BadZipFile as e:
        raise ModelPackageError(f'Not a zip archive: {e}') from e


def safeExtract(data: bytes, dest: Union[str, os.PathLike]) -> ModelPackageManifest:
    """
    Extract a package archive into *dest*, checking every member first.

    :param data: the archive
    :param dest: existing (normally empty) directory
    :return: the manifest of the package
    :raises ModelPackageError: if the archive is invalid, has no valid manifest, or contains unsafe
                               paths or links (nothing is extracted then)
    """
    manifest = readArchiveManifest(data)
    dest = Path(dest)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = zf.infolist()
        for info in infos:
            _checkMember(info)
        for info in infos:
            target = Path(zf.extract(info, dest))
            # zipfile drops permissions; keep the executable bit of scripts
            mode = (info.external_attr >> 16) & 0o777
            if mode and not info.is_dir():
                os.chmod(target, mode)
    return manifest


class ModelRegistry(abc.ABC):
    """Where execution servers find model packages (see the module documentation)."""

    @abc.abstractmethod
    def resolve(self, modelID: str, version: Optional[str] = None) -> PackageRef:
        """
        Find a package.

        :param modelID: model ID
        :param version: version; None: the latest one (see :func:`versionKey`)
        :raises ModelPackageNotFound: if there is no such package
        """

    @abc.abstractmethod
    def download(self, ref: PackageRef) -> bytes:
        """
        Return the archive of a package found by :meth:`resolve`.

        The caller verifies it against :attr:`PackageRef.digest`.
        """

    def describe(self) -> str:
        """Return a short description, for logs."""
        return type(self).__name__


class DirectoryRegistry(ModelRegistry):
    """
    Packages in a local directory: package directories (with ``mupif-model.toml``) and package
    archives (``*.zip``), anywhere below *root*.

    The directory is scanned on every :meth:`resolve`, so packages added meanwhile are found. Two
    packages with the same ID and version are an error (which one would run would be arbitrary).

    :param root: the directory
    """

    def __init__(self, root: Union[str, os.PathLike]):
        self.root = Path(root)

    def describe(self) -> str:
        return f'directory {self.root}'

    def _scan(self) -> list[tuple[ModelPackageManifest, Path]]:
        """Return the manifests and paths of all packages below :attr:`root`; invalid ones are logged and skipped."""
        found = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = sorted(d for d in dirs if d not in ARCHIVE_EXCLUDE_DIRS)
            here = Path(root)
            if MANIFEST_NAME in files:
                try:
                    found.append((ModelPackageManifest.fromToml((here / MANIFEST_NAME).read_bytes()), here))
                except ModelPackageError as e:
                    log.warning(f'Skipping model package {here}: {e}')
                # a package directory: its subdirectories are its contents, not other packages
                dirs[:] = []
                continue
            for f in sorted(files):
                if f.endswith('.zip'):
                    try:
                        found.append((readArchiveManifest((here / f).read_bytes()), here / f))
                    except ModelPackageError as e:
                        log.warning(f'Skipping {here / f}: {e}')
        return found

    def resolve(self, modelID: str, version: Optional[str] = None) -> PackageRef:
        matches = [(m, p) for m, p in self._scan() if m.ID == modelID and (version is None or m.Version == version)]
        if not matches:
            raise ModelPackageNotFound(f'No model package {modelID}' + (f'@{version}' if version else '') + f' in {self.describe()}')
        matches.sort(key=lambda mp: versionKey(mp[0].Version))
        manifest, path = matches[-1]
        dups = [str(p) for m, p in matches if m.Version == manifest.Version]
        if len(dups) > 1:
            raise ModelPackageError(f'Model package {manifest.key()} found more than once: {", ".join(dups)}')
        return PackageRef(manifest=manifest, digest=digest(self._archive(path)), location=str(path))

    def download(self, ref: PackageRef) -> bytes:
        return self._archive(Path(ref.location))

    @staticmethod
    def _archive(path: Path) -> bytes:
        """Return the archive of a package directory (built) or archive file (read)."""
        return path.read_bytes() if path.is_file() else buildArchive(path)


def main(argv: Optional[list[str]] = None) -> int:
    """
    Command line: ``python -m mupif.modelpackage {build,publish,show} ...``.

    * ``build <dir> [-o <zip>]`` -- check a package directory, pack it, print its digest;
    * ``publish <dir|zip>`` -- publish a package to mupifDB (an administrator account, see
      :mod:`mupif.mupifdbclient` for the connection settings);
    * ``show <id> [<version>]`` -- the package an execution server would run.
    """
    import argparse
    import json
    parser = argparse.ArgumentParser(prog='python -m mupif.modelpackage', description='MuPIF model packages (see mupif.modelpackage).')
    parser.add_argument('--server', help='mupifDB API (default: $MUPIFDB_REST_SERVER)')
    sub = parser.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build', help='check and pack a package directory; print its digest')
    b.add_argument('directory')
    b.add_argument('-o', '--output', help='write the archive to this file')
    p = sub.add_parser('publish', help='publish a package (directory or zip) to mupifDB')
    p.add_argument('package')
    s = sub.add_parser('show', help='show a published package')
    s.add_argument('id')
    s.add_argument('version', nargs='?')
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'build':
            data = buildArchive(args.directory)
            manifest = readArchiveManifest(data)
            if args.output:
                Path(args.output).write_bytes(data)
            print(f'{manifest.key()} {digest(data)} ({len(data)} bytes)')
            return 0
        from .mupifdbclient import MupifDBClient, MupifDBRegistry
        registry = MupifDBRegistry(MupifDBClient(args.server))
        if args.cmd == 'publish':
            rec = registry.publish(args.package)
            print(f'Published {rec["ID"]}@{rec["Version"]} {rec["Digest"]}')
        else:
            ref = registry.resolve(args.id, args.version)
            print(json.dumps({**ref.describe(), 'Manifest': ref.manifest.model_dump()}, indent=2))
        return 0
    except Exception as e:  # a message, not a traceback, for the command line
        print(f'Error: {e}')
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
