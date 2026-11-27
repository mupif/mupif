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
Launchers: how a model server starts the process of a job.

A model server (:class:`mupif.ModelServer`) runs every job in its own process. That process runs a
Python interpreter with the *bootstrap arguments* chosen by the model server::

    -c 'import mupif; mupif.ModelServer._spawnedProcessPopen()' - <pickled arguments>

The child then instantiates the model, registers it in the nameserver under the job ID and reports
its URI back (see :meth:`mupif.ModelServer._spawnedProcessPopen`). That contract is the same for
every launcher; a launcher only decides **which interpreter, in which environment** runs it:

* :class:`LocalPythonLauncher` -- the interpreter of the model server itself, with the server's
  ``sys.path`` (the model must be importable by the server). This is what model servers always did.
* :class:`PixiLauncher` -- the interpreter of the pixi environment of a model package (see
  :mod:`mupif.modelpackage`), so that the model brings its own dependencies; used by execution
  servers (:mod:`mupif.executionserver`);
* :class:`ApptainerLauncher` -- the interpreter of a container image of a model package, run by
  Apptainer (Singularity): the whole userland comes with the model; no root needed, available on
  most HPC systems.

A launcher may also add environment variables and directories to ``PATH`` of the job: this is how an
execution server hands *host capabilities* (e.g. the installation directory and licence server of a
proprietary solver) to a model.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

log = logging.getLogger(__name__)


class Launcher:
    """
    Base of launchers: builds the command line and the environment of a job process.

    Subclasses override :meth:`command` (the interpreter running the bootstrap arguments) and, if
    needed, :meth:`prepare` (making the environment ready before the first job) and :meth:`env`.

    :param extraEnv: environment variables set for the job (they override inherited ones)
    :param extraPath: directories prepended to ``PATH`` of the job, in this order
    """
    #: short name of the launcher, for logs
    name = 'base'

    def __init__(self, *, extraEnv: Optional[Mapping[str, str]] = None, extraPath: Optional[Sequence[str]] = None):
        self.extraEnv = dict(extraEnv or {})
        self.extraPath = list(extraPath or [])

    def prepare(self) -> None:
        """
        Make the environment ready to start jobs (e.g. install it); called before a job is started.

        It may take long (minutes, for an environment to be downloaded and installed): the model
        server calls it before it starts waiting for the job (``jobStartTimeout``). It must be
        idempotent and cheap once done. The base implementation does nothing.

        :raises Exception: if the environment cannot be prepared (the job is not started)
        """

    def command(self, bootstrap: Sequence[str], *, workDir: Optional[str] = None) -> list[str]:
        """
        Return the command line of a job process.

        :param bootstrap: arguments of the Python interpreter (``-c <code> - <pickled arguments>``)
        :param workDir: the job's work directory, where the job reports its URI (``_mupif_uri``)
                        and works; a launcher isolating the job's file system must make it visible
                        to the job at the same path
        :return: the complete command line (the interpreter first)
        """
        raise NotImplementedError

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        """
        Return the environment of a job process.

        The base implementation applies :attr:`extraEnv` and prepends :attr:`extraPath` to ``PATH``;
        subclasses calling it may add or remove variables before or after.

        :param base: the environment to start from: the server's environment with the job's
                     ``MUPIF_*`` variables (logging: ``MUPIF_LOG_*``) set by the model server
        :return: a new dictionary; *base* is not changed
        """
        env = dict(base)
        env.update(self.extraEnv)
        if self.extraPath:
            env['PATH'] = os.pathsep.join(self.extraPath + ([env['PATH']] if env.get('PATH') else []))
        return env

    def describe(self) -> str:
        """Return a short description, for logs."""
        return self.name


class LocalPythonLauncher(Launcher):
    """
    Run a job with the interpreter of the model server itself (the behaviour of model servers so far).

    The job inherits the server's environment. ``PYTHONPATH`` is set to the server's ``sys.path``
    (followed by the inherited ``PYTHONPATH``): a model class may be importable in the server only
    because the server script changed ``sys.path``, and the job must be able to import it as well.

    :param pythonPath: directories put in front of ``PYTHONPATH`` of the job, before the server's
                       ``sys.path`` (e.g. the directory of a model package)
    :param extraEnv: see :class:`Launcher`
    :param extraPath: see :class:`Launcher`
    """
    name = 'python'

    def __init__(self, *, pythonPath: Optional[Sequence[str]] = None, **kw):
        super().__init__(**kw)
        self.pythonPath = list(pythonPath or [])

    def command(self, bootstrap: Sequence[str], *, workDir: Optional[str] = None) -> list[str]:
        return [sys.executable, *bootstrap]

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        env = super().env(base)
        env['PYTHONPATH'] = os.pathsep.join(self.pythonPath + list(sys.path)) + ((os.pathsep + base['PYTHONPATH']) if base.get('PYTHONPATH') else '')
        return env


class PixiLauncher(Launcher):
    """
    Run a job in the pixi environment of a model package.

    :meth:`prepare` installs the environment exactly as locked (``pixi install --locked``) and reads
    its *activation* (``pixi shell-hook --json``: ``PATH``, ``CONDA_PREFIX`` and the variables set by
    activation scripts of the packages). Jobs then run the environment's own ``python`` directly,
    with that activation applied: the job process is the model's interpreter itself, not ``pixi
    run`` in front of it, so that terminating the job (SIGTERM from the model server) reaches the
    model and nothing is left running.

    The job environment does not inherit ``PYTHONPATH``/``PYTHONHOME`` of the server (they would
    mix the server's packages into the model's environment); ``PYTHONPATH`` is the package directory,
    from which the model's entry point is imported.

    The pixi executable is taken from *pixi*, else ``$PIXI_EXE``, else ``pixi`` in ``PATH``, else
    ``~/.pixi/bin/pixi`` (the default installation).

    :param packageDir: the package directory, containing ``pixi.toml`` (or ``pyproject.toml`` with
                       a pixi section) and ``pixi.lock``
    :param environment: name of the pixi environment
    :param pixi: path of the pixi executable
    :param installTimeout: seconds ``pixi install`` may take
    :param extraEnv: see :class:`Launcher` (host capabilities)
    :param extraPath: see :class:`Launcher` (host capabilities)
    """
    name = 'pixi'

    def __init__(self, packageDir, *, environment: str = 'default', pixi: Optional[str] = None, installTimeout: float = 3600., **kw):
        super().__init__(**kw)
        self.packageDir = Path(packageDir)
        self.environment = environment
        self.pixi = pixi or self.findPixi()
        self.installTimeout = installTimeout
        #: activation variables of the environment (set by :meth:`prepare`)
        self.activation: Optional[dict[str, str]] = None

    @staticmethod
    def findPixi() -> Optional[str]:
        """Return the pixi executable (see the class documentation), or None if there is none."""
        for cand in (os.environ.get('PIXI_EXE'), shutil.which('pixi'), str(Path.home() / '.pixi' / 'bin' / 'pixi')):
            if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
        return None

    def describe(self) -> str:
        return f'pixi environment {self.environment!r} of {self.packageDir}'

    def _manifest(self) -> Path:
        for name in ('pixi.toml', 'pyproject.toml'):
            if (self.packageDir / name).is_file():
                return self.packageDir / name
        raise RuntimeError(f'{self.packageDir} has no pixi.toml (nor pyproject.toml)')

    def _run(self, args: list[str], timeout: float) -> str:
        """Run pixi with *args*; return its standard output; raise with its output if it fails."""
        if not self.pixi:
            raise RuntimeError('pixi not found (set PIXI_EXE, or put pixi into PATH)')
        cmd = [self.pixi, *args, '--manifest-path', str(self._manifest())]
        log.debug(f'Running {cmd}')
        # pixi must not see the server's Python setup either
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
        res = subprocess.run(cmd, cwd=self.packageDir, env=env, capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            raise RuntimeError(f'{" ".join(cmd[:2])} failed with exit status {res.returncode}:\n{res.stderr[-4000:]}')
        return res.stdout

    def prepare(self) -> None:
        """
        Install the environment as locked and read its activation; does nothing once done.

        ``--locked``: the lock file must be up to date with ``pixi.toml``; the environment is never
        re-solved on the server, so that every server runs exactly what was published.
        """
        if self.activation is not None:
            return
        self._run(['install', '--locked', '-e', self.environment], timeout=self.installTimeout)
        out = self._run(['shell-hook', '--json', '--locked', '-e', self.environment], timeout=300.)
        try:
            activation = json.loads(out)['environment_variables']
        except (ValueError, KeyError, TypeError) as e:
            raise RuntimeError(f'Unexpected output of pixi shell-hook --json: {out[:1000]!r}') from e
        if not activation.get('CONDA_PREFIX'):
            raise RuntimeError(f'pixi shell-hook gave no CONDA_PREFIX for {self.describe()}')
        self.activation = {str(k): str(v) for k, v in activation.items()}
        log.info(f'Prepared {self.describe()}: {self.activation["CONDA_PREFIX"]}')

    def python(self) -> str:
        """Return the interpreter of the environment (after :meth:`prepare`)."""
        if self.activation is None:
            raise RuntimeError('PixiLauncher.prepare() must be called first')
        prefix = Path(self.activation['CONDA_PREFIX'])
        return str(prefix / 'python.exe') if sys.platform.startswith('win') else str(prefix / 'bin' / 'python')

    def command(self, bootstrap: Sequence[str], *, workDir: Optional[str] = None) -> list[str]:
        return [self.python(), *bootstrap]

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        if self.activation is None:
            raise RuntimeError('PixiLauncher.prepare() must be called first')
        env = {k: v for k, v in base.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
        env.update(self.activation)
        env['PYTHONPATH'] = str(self.packageDir)
        # host capabilities last, so that they are not overridden by the activation
        return super().env(env)


class ApptainerLauncher(Launcher):
    """
    Run a job in the container image of a model package, with Apptainer (or Singularity).

    :meth:`prepare` obtains the image once into ``<packageDir>/.apptainer/image.sif``:

    * ``docker://...@sha256:<hex>``, ``oras://...@sha256:<hex>`` -- ``apptainer pull`` (pinned by
      digest: the registry content is verified by it); Apptainer's layer cache is not used
      (``--disable-cache``), the SIF in the package cache is what is kept;
    * ``https://...``, ``file:///...`` -- downloaded or copied, and verified against *imageDigest*
      (sha256 of the SIF file); a mismatch is an error and nothing is kept.

    A job runs ``apptainer exec`` with:

    * ``--contain --cleanenv``: the container sees its own userland, a private ``/tmp`` and home,
      and none of the server's environment variables (its ``PYTHONPATH`` would mix the server's
      packages into the image's Python);
    * the job's work directory bound at the same path (the job reports its URI and works there);
    * the package directory bound read-only at ``/mupif/package``, which is ``PYTHONPATH``: the
      model's entry point may come with the package or be installed in the image;
    * the job's ``MUPIF_*`` variables and the host capabilities' variables passed in
      (``APPTAINERENV_<name>``), the capabilities' ``PATH`` entries prepended
      (``APPTAINERENV_PREPEND_PATH``), their directories (*binds*) bound read-only at the same path;
    * ``--nv`` if *gpu*.

    The container shares the host's network (Apptainer's default), so the model's Pyro daemon is
    reachable as from any job. It does not get a PID namespace (``--pid``): the model's Python would
    be process 1 there, which ignores the model server's SIGTERM; without it, ``apptainer exec``
    forwards the signal to the model.

    :param packageDir: the package directory (in the execution server's cache)
    :param image: the image (see :class:`mupif.modelpackage.RuntimeSpec`)
    :param imageDigest: ``sha256:<hex>`` of the SIF file, for ``https://`` and ``file:///`` images
    :param gpu: pass ``--nv``
    :param python: the interpreter in the image
    :param binds: host directories bound read-only into the container at the same path
    :param apptainer: the apptainer executable (default: ``$APPTAINER_EXE``, else ``apptainer`` or
                      ``singularity`` in ``PATH``)
    :param pullTimeout: seconds obtaining the image may take
    :param extraEnv: variables passed into the container (host capabilities)
    :param extraPath: directories prepended to ``PATH`` in the container (host capabilities)
    """
    name = 'apptainer'
    #: where the package directory is mounted in the container
    CONTAINER_PACKAGE_DIR = '/mupif/package'

    def __init__(self, packageDir, *, image: str, imageDigest: str = '', gpu: bool = False, python: str = 'python3',
                 binds: Sequence[str] = (), apptainer: Optional[str] = None, pullTimeout: float = 3600., **kw):
        super().__init__(**kw)
        self.packageDir = Path(packageDir)
        self.image = image
        self.imageDigest = imageDigest
        self.gpu = gpu
        self.python = python
        self.binds = list(binds)
        self.apptainer = apptainer or self.findApptainer()
        self.pullTimeout = pullTimeout
        for path in [str(self.packageDir), *self.binds]:
            self._checkBindPath(path)

    @staticmethod
    def findApptainer() -> Optional[str]:
        """Return the apptainer (or singularity) executable, or None if there is none."""
        for cand in (os.environ.get('APPTAINER_EXE'), shutil.which('apptainer'), shutil.which('singularity')):
            if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
        return None

    @staticmethod
    def _checkBindPath(path: str) -> None:
        """Refuse paths which cannot be written in a ``--bind`` specification (``src:dst:opts``, comma-separated)."""
        if ':' in path or ',' in path:
            raise ValueError(f'Path {path!r} cannot be bound into a container (contains ":" or ",")')

    @property
    def sif(self) -> Path:
        """The image file of the package."""
        return self.packageDir / '.apptainer' / 'image.sif'

    def describe(self) -> str:
        return f'apptainer image {self.image} of {self.packageDir}'

    def prepare(self) -> None:
        """Obtain and verify the image (see the class documentation); does nothing once done."""
        if self.sif.exists():
            return
        if not self.apptainer:
            raise RuntimeError('apptainer not found (set APPTAINER_EXE, or put apptainer into PATH)')
        self.sif.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.sif.with_name(f'.image-{os.getpid()}-{id(self)}.sif')
        try:
            if self.image.startswith(('docker://', 'oras://')):
                self._pull(tmp)
            else:
                self._fetchVerified(tmp)
            os.rename(tmp, self.sif)
        finally:
            if tmp.exists():
                tmp.unlink()
        log.info(f'Prepared {self.describe()}: {self.sif} ({self.sif.stat().st_size} bytes)')

    def _hostEnv(self, base: Mapping[str, str]) -> dict[str, str]:
        """The environment of the apptainer process itself: without variables meant for containers of the server."""
        return {k: v for k, v in base.items() if not k.startswith(('APPTAINERENV_', 'SINGULARITYENV_'))}

    def _pull(self, dest: Path) -> None:
        cmd = [self.apptainer, 'pull', '--disable-cache', str(dest), self.image]
        log.info(f'Pulling {self.image}')
        res = subprocess.run(cmd, env=self._hostEnv(os.environ), capture_output=True, text=True, timeout=self.pullTimeout)
        if res.returncode != 0:
            raise RuntimeError(f'apptainer pull {self.image} failed with exit status {res.returncode}:\n{res.stderr[-4000:]}')

    def _fetchVerified(self, dest: Path) -> None:
        """Download or copy a SIF file into *dest*, verifying its sha256 (*imageDigest*)."""
        import hashlib
        import urllib.parse
        h = hashlib.sha256()
        with open(dest, 'wb') as out:
            if self.image.startswith('file:///'):
                src = urllib.parse.unquote(urllib.parse.urlparse(self.image).path)
                with open(src, 'rb') as f:
                    while chunk := f.read(2**20):
                        h.update(chunk)
                        out.write(chunk)
            else:
                import requests
                with requests.get(self.image, stream=True, timeout=(10, 300)) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(2**20):
                        h.update(chunk)
                        out.write(chunk)
        got = 'sha256:' + h.hexdigest()
        if got != self.imageDigest:
            raise RuntimeError(f'Image {self.image} has digest {got}, the package requires {self.imageDigest}; refusing it')

    def command(self, bootstrap: Sequence[str], *, workDir: Optional[str] = None) -> list[str]:
        if not self.apptainer:
            raise RuntimeError('apptainer not found (set APPTAINER_EXE, or put apptainer into PATH)')
        if workDir is None:
            raise ValueError('ApptainerLauncher needs the work directory of the job')
        self._checkBindPath(workDir)
        cmd = [self.apptainer, 'exec', '--contain', '--cleanenv']
        if self.gpu:
            cmd.append('--nv')
        cmd += ['--bind', f'{workDir}:{workDir}', '--bind', f'{self.packageDir}:{self.CONTAINER_PACKAGE_DIR}:ro']
        for b in self.binds:
            cmd += ['--bind', f'{b}:{b}:ro']
        return cmd + [str(self.sif), self.python, *bootstrap]

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        """
        The environment of ``apptainer exec``; what the job sees is passed as ``APPTAINERENV_*``.

        Passed into the container: the job's ``MUPIF_*`` variables (logging), :attr:`extraEnv`,
        ``PYTHONPATH`` (the package directory in the container) and :attr:`extraPath`, prepended
        to the container's ``PATH``.
        """
        env = self._hostEnv(base)
        inside = {k: v for k, v in base.items() if k.startswith('MUPIF_')}
        inside.update(self.extraEnv)
        inside['PYTHONPATH'] = self.CONTAINER_PACKAGE_DIR
        if self.extraPath:
            inside['PREPEND_PATH'] = os.pathsep.join(self.extraPath)
        env.update({f'APPTAINERENV_{k}': v for k, v in inside.items()})
        return env
