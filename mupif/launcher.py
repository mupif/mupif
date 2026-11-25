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
* other launchers (see :mod:`mupif.executionserver`) run the interpreter of a separate environment
  of a model package, e.g. a pixi environment, so that the model brings its own dependencies.

A launcher may also add environment variables and directories to ``PATH`` of the job: this is how an
execution server hands *host capabilities* (e.g. the installation directory and licence server of a
proprietary solver) to a model.
"""

from __future__ import annotations

import os
import sys
from typing import Mapping, Optional, Sequence


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

    def command(self, bootstrap: Sequence[str]) -> list[str]:
        """
        Return the command line of a job process.

        :param bootstrap: arguments of the Python interpreter (``-c <code> - <pickled arguments>``)
        :return: the complete command line (the interpreter first)
        """
        raise NotImplementedError

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        """
        Return the environment of a job process.

        The base implementation applies :attr:`extraEnv` and prepends :attr:`extraPath` to ``PATH``;
        subclasses calling it may add or remove variables before or after.

        :param base: the environment to start from (normally a copy of ``os.environ``)
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

    def command(self, bootstrap: Sequence[str]) -> list[str]:
        return [sys.executable, *bootstrap]

    def env(self, base: Mapping[str, str]) -> dict[str, str]:
        env = super().env(base)
        env['PYTHONPATH'] = os.pathsep.join(self.pythonPath + list(sys.path)) + ((os.pathsep + base['PYTHONPATH']) if base.get('PYTHONPATH') else '')
        return env
