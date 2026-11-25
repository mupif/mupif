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
Model packages published to mupifDB: a registry for execution servers, and publishing.

mupifDB keeps model packages in its collection ``Models`` (one record per ID and version, with the
digest of the archive) and their archives in GridFS. This module talks to its REST API directly
(only ``requests`` is needed), so that execution server hosts need mupif and pixi, not mupifDB:

* :class:`MupifDBRegistry` -- a :class:`mupif.modelpackage.ModelRegistry` resolving model IDs
  (``GET api/models/{id}/versions/{version|latest}``) and downloading archives
  (``GET api/file/{GridFSID}``); used by :class:`mupif.ExecutionServer`;
* :meth:`MupifDBRegistry.publish` -- uploads a package (``POST api/models``; an administrator
  account is required): the API validates the manifest, computes the digest and refuses a version
  published before.

Connection settings follow mupifDB's own client: the API at ``$MUPIFDB_REST_SERVER`` (default
``http://127.0.0.1:8005/``), the account from the JSON file ``$API_CREDENTIALS_FILE``
(``{"username": ..., "password": ...}``). Without an account, requests are sent unauthenticated
(the API refuses them unless it runs without authentication).

From the command line, see ``python -m mupif.modelpackage --help`` (``publish``, ``show``).
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional, Union

import requests

from .modelpackage import (ModelPackageError, ModelPackageManifest, ModelPackageNotFound, ModelRegistry, PackageRef,
                           RuntimeSpec, buildArchive, readArchiveManifest)

log = logging.getLogger(__name__)

DEFAULT_SERVER = 'http://127.0.0.1:8005/'


class MupifDBError(Exception):
    """The mupifDB API refused a request or cannot be reached."""


class MupifDBClient:
    """
    Minimal client of the mupifDB REST API: authentication and requests.

    Logs in with the account (``POST api/login``), sends the bearer token with every request, logs
    in again shortly before the token expires or when the API answers 401. Thread safe.

    :param server: URL of the API server (default: ``$MUPIFDB_REST_SERVER``, else :data:`DEFAULT_SERVER`)
    :param username: account; default: from *credentialsFile*
    :param password: password of the account
    :param credentialsFile: JSON file with ``username`` and ``password`` (default: ``$API_CREDENTIALS_FILE``)
    :param timeout: ``(connect, read)`` timeouts of requests in seconds
    """

    def __init__(self, server: Optional[str] = None, *, username: Optional[str] = None, password: Optional[str] = None,
                 credentialsFile: Optional[str] = None, timeout: tuple[float, float] = (5., 120.)):
        server = server or os.environ.get('MUPIFDB_REST_SERVER') or DEFAULT_SERVER
        self.server = server if server.endswith('/') else server + '/'
        if username is None:
            credentialsFile = credentialsFile or os.environ.get('API_CREDENTIALS_FILE')
            if credentialsFile and os.path.exists(credentialsFile):
                with open(credentialsFile) as f:
                    cred = json.load(f)
                username, password = cred['username'], cred['password']
        self.username = username
        self.password = password
        self.timeout = timeout
        self._lock = threading.Lock()
        self._token: Optional[str] = None
        #: time.time() after which the token is renewed (a minute before it expires)
        self._tokenRenewAt = 0.

    def url(self, path: str) -> str:
        """Return the URL of an API path (``models/...`` -> ``<server>api/models/...``)."""
        return f'{self.server}api/{path.lstrip("/")}'

    def _login(self) -> None:
        """Obtain a token (lock held)."""
        try:
            r = requests.post(self.url('login'), data={'username': self.username, 'password': self.password}, timeout=self.timeout)
        except requests.RequestException as e:
            raise MupifDBError(f'Cannot reach the mupifDB API at {self.server}: {e}') from e
        if r.status_code != 200:
            raise MupifDBError(f'Login to the mupifDB API as {self.username} failed ({r.status_code}): {r.text[:500]}')
        data = r.json()
        self._token = data['access_token']
        expires = data.get('expires_at')
        try:
            self._tokenRenewAt = datetime.datetime.fromisoformat(expires).timestamp() - 60 if expires else time.time() + 300
        except ValueError:
            self._tokenRenewAt = time.time() + 300

    def _headers(self, renew: bool = False) -> dict[str, str]:
        if not self.username:
            return {}
        with self._lock:
            if renew or self._token is None or time.time() > self._tokenRenewAt:
                self._login()
            return {'Authorization': f'Bearer {self._token}'}

    def request(self, method: str, path: str, **kw) -> requests.Response:
        """
        Send a request; log in again and repeat it once if the API answers 401.

        :return: the response (any status; see :meth:`check`)
        :raises MupifDBError: if the API cannot be reached
        """
        kw.setdefault('timeout', self.timeout)
        for attempt in range(2):
            try:
                r = requests.request(method, self.url(path), headers=self._headers(renew=attempt > 0), **kw)
            except requests.RequestException as e:
                raise MupifDBError(f'Cannot reach the mupifDB API at {self.server}: {e}') from e
            if r.status_code != 401 or not self.username:
                return r
        return r

    @staticmethod
    def check(r: requests.Response, what: str) -> requests.Response:
        """Raise :class:`MupifDBError` describing *what* failed unless the response is a success."""
        if not r.ok:
            try:
                detail = r.json().get('detail', r.text)
            except ValueError:
                detail = r.text
            raise MupifDBError(f'{what}: mupifDB API answered {r.status_code}: {str(detail)[:1000]}')
        return r


def _manifestOfRecord(rec: dict[str, Any]) -> ModelPackageManifest:
    """Return the manifest stored in a mupifDB model package record."""
    return ModelPackageManifest(ID=rec['ID'], Version=rec['Version'], Entrypoint=rec['Entrypoint'],
                                Runtime=RuntimeSpec.model_validate(rec['Runtime']),
                                RequiresHost=rec.get('RequiresHost') or [], Description=rec.get('Description') or '')


class MupifDBRegistry(ModelRegistry):
    """
    Model packages published to mupifDB (see the module documentation).

    :param client: API client; default: :class:`MupifDBClient` with the default settings
    """

    def __init__(self, client: Optional[MupifDBClient] = None):
        self.client = client or MupifDBClient()

    def describe(self) -> str:
        return f'mupifDB {self.client.server}'

    def resolve(self, modelID: str, version: Optional[str] = None) -> PackageRef:
        q = urllib.parse.quote
        r = self.client.request('GET', f'models/{q(modelID, safe="")}/versions/{q(version or "latest", safe="")}')
        if r.status_code == 404:
            raise ModelPackageNotFound(f'No model package {modelID}' + (f'@{version}' if version else '') + f' in {self.describe()}')
        rec = self.client.check(r, f'Resolving model package {modelID}@{version or "latest"}').json()
        return PackageRef(manifest=_manifestOfRecord(rec), digest=rec['Digest'], location=rec['GridFSID'])

    def download(self, ref: PackageRef) -> bytes:
        r = self.client.request('GET', f'file/{urllib.parse.quote(ref.location, safe="")}')
        return self.client.check(r, f'Downloading model package {ref.manifest.key()}').content

    def listPackages(self, modelID: Optional[str] = None) -> list[dict[str, Any]]:
        """Return the records of the published packages (of one model ID, if given)."""
        r = self.client.request('GET', 'models', params={'id': modelID} if modelID else {})
        return self.client.check(r, 'Listing model packages').json()

    def publish(self, package: Union[str, os.PathLike, bytes]) -> dict[str, Any]:
        """
        Publish a model package.

        :param package: a package directory (packed by :func:`~mupif.modelpackage.buildArchive`), a
                        zip archive file, or the archive itself
        :return: the record created by mupifDB (with ``Digest`` and ``GridFSID``)
        :raises ModelPackageError: if the package is invalid
        :raises MupifDBError: if the API refuses it (e.g. 409: this version is published already;
                              403: the account is not an administrator)
        """
        if isinstance(package, bytes):
            data = package
        elif Path(package).is_dir():
            data = buildArchive(package)
        else:
            data = Path(package).read_bytes()
        manifest = readArchiveManifest(data)
        r = self.client.request('POST', 'models', files={'package': (f'{manifest.ID}-{manifest.Version}.zip', data, 'application/zip')})
        rec = self.client.check(r, f'Publishing model package {manifest.key()}').json()
        log.info(f'Published model package {manifest.key()} ({rec.get("Digest")})')
        return rec
