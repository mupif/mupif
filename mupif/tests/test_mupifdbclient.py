"""
Tests of :mod:`mupif.mupifdbclient` against a fake mupifDB API (a small HTTP server in a thread),
and of the command line of :mod:`mupif.modelpackage`.

The fake implements the endpoints the client uses, as mupifDB does: form login with a bearer token,
the model package records (``api/models``), file download (``api/file/{id}``).
"""

import email.parser
import email.policy
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mupif import modelpackage as mpk
from mupif.mupifdbclient import MupifDBClient, MupifDBError, MupifDBRegistry
from mupif.packagecache import PackageCache

from .test_modelpackage import makePackage


class FakeAPI:
    """State of the fake API: accounts, valid tokens, records, files; counts logins."""
    def __init__(self):
        self.users = {'admin@x': ('pw', True), 'server@x': ('pw', False)}
        self.tokens = {}  # token -> user
        self.records = []
        self.files = {}
        self.logins = 0


def makeHandler(api: FakeAPI):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body, ctype='application/json'):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def user(self):
            auth = self.headers.get('Authorization', '')
            return api.tokens.get(auth[len('Bearer '):]) if auth.startswith('Bearer ') else None

        def body(self):
            return self.rfile.read(int(self.headers.get('Content-Length', 0)))

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            if path == '/api/login':
                form = urllib.parse.parse_qs(self.body().decode())
                u, p = form.get('username', [''])[0], form.get('password', [''])[0]
                if api.users.get(u, (None,))[0] != p:
                    return self.reply(400, {'detail': 'Incorrect username or password'})
                api.logins += 1
                tok = f'tok{api.logins}'
                api.tokens[tok] = u
                return self.reply(200, {'access_token': tok, 'token_type': 'bearer', 'expires_at': '2999-01-01T00:00:00+00:00'})
            if path == '/api/models':
                u = self.user()
                if u is None:
                    return self.reply(401, {'detail': 'Not authenticated'})
                if not api.users[u][1]:
                    return self.reply(403, {'detail': "You don't have permission to perform this action."})
                msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(
                    b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + self.body())
                part = next(p for p in msg.iter_parts() if p.get_param('name', header='content-disposition') == 'package')
                data = part.get_payload(decode=True)
                m = mpk.readArchiveManifest(data)
                if any(r['ID'] == m.ID and r['Version'] == m.Version for r in api.records):
                    return self.reply(409, {'detail': f'{m.key()} is published already'})
                gid = f'{len(api.files):024x}'
                api.files[gid] = data
                rec = {**m.model_dump(), 'Digest': mpk.digest(data), 'GridFSID': gid, 'FileName': part.get_filename(), 'Size': len(data), 'Publisher': u}
                api.records.append(rec)
                return self.reply(200, rec)
            self.reply(404, {'detail': 'not found'})

        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            parts = [urllib.parse.unquote(p) for p in url.path.split('/')]
            if self.user() is None:
                return self.reply(401, {'detail': 'Not authenticated'})
            if parts[1:3] == ['api', 'models'] and len(parts) == 3:
                ids = urllib.parse.parse_qs(url.query).get('id')
                return self.reply(200, [r for r in api.records if not ids or r['ID'] == ids[0]])
            if parts[1:3] == ['api', 'models'] and len(parts) == 6 and parts[4] == 'versions':
                recs = [r for r in api.records if r['ID'] == parts[3] and parts[5] in ('latest', r['Version'])]
                if not recs:
                    return self.reply(404, {'detail': 'no such model package'})
                return self.reply(200, max(recs, key=lambda r: mpk.versionKey(r['Version'])))
            if parts[1:3] == ['api', 'file'] and parts[3] in api.files:
                return self.reply(200, api.files[parts[3]], 'application/zip')
            self.reply(404, {'detail': 'not found'})
    return Handler


@pytest.fixture
def api():
    state = FakeAPI()
    srv = ThreadingHTTPServer(('127.0.0.1', 0), makeHandler(state))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    state.url = f'http://127.0.0.1:{srv.server_address[1]}'
    yield state
    srv.shutdown()


def registry(api, user='server@x', password='pw'):
    return MupifDBRegistry(MupifDBClient(api.url, username=user, password=password))


def test_publish_resolve_download(api, tmp_path):
    admin = registry(api, 'admin@x')
    rec1 = admin.publish(makePackage(tmp_path / 'v1', version='1.9'))
    rec2 = admin.publish(mpk.buildArchive(makePackage(tmp_path / 'v2', version='1.10', code='VALUE = 2\n')))
    assert rec1['Digest'] == mpk.digest(mpk.buildArchive(tmp_path / 'v1'))
    srv = registry(api)
    ref = srv.resolve('my-model')
    assert ref.version == '1.10' and ref.digest == rec2['Digest'] and ref.location == rec2['GridFSID']
    assert ref.manifest.Entrypoint == 'mymodel.model:MyModel' and ref.manifest.Runtime.Type == 'python'
    assert srv.resolve('my-model', '1.9').digest == rec1['Digest']
    assert mpk.digest(srv.download(ref)) == ref.digest
    assert [r['Version'] for r in srv.listPackages('my-model')] == ['1.9', '1.10']
    with pytest.raises(mpk.ModelPackageNotFound):
        srv.resolve('my-model', '7')
    with pytest.raises(mpk.ModelPackageNotFound):
        srv.resolve('nope')
    # one login per client, reused
    assert api.logins == 2


def test_publish_refusals(api, tmp_path):
    pkg = makePackage(tmp_path / 'p')
    registry(api, 'admin@x').publish(pkg)
    with pytest.raises(MupifDBError, match='409'):
        registry(api, 'admin@x').publish(pkg)
    with pytest.raises(MupifDBError, match='403'):
        registry(api).publish(makePackage(tmp_path / 'q', version='2'))
    with pytest.raises(MupifDBError, match='Login'):
        registry(api, 'admin@x', 'wrong').publish(pkg)
    (tmp_path / 'empty').mkdir()
    with pytest.raises(mpk.ModelPackageError):
        registry(api, 'admin@x').publish(tmp_path / 'empty')


def test_token_renewed_after_401(api, tmp_path):
    registry(api, 'admin@x').publish(makePackage(tmp_path / 'p'))
    srv = registry(api)
    srv.resolve('my-model')
    api.tokens.clear()  # tokens revoked (API restarted, session expired)
    assert srv.resolve('my-model').version == '1.0'


def test_unreachable_api():
    reg = MupifDBRegistry(MupifDBClient('http://127.0.0.1:9', username='u', password='p', timeout=(1, 1)))
    with pytest.raises(MupifDBError, match='Cannot reach'):
        reg.resolve('x')


def test_credentials_file(api, tmp_path, monkeypatch):
    cred = tmp_path / 'cred.json'
    cred.write_text(json.dumps({'username': 'server@x', 'password': 'pw'}))
    monkeypatch.setenv('API_CREDENTIALS_FILE', str(cred))
    monkeypatch.setenv('MUPIFDB_REST_SERVER', api.url)
    c = MupifDBClient()
    assert (c.server, c.username) == (api.url + '/', 'server@x')
    assert c.url('models') == api.url + '/api/models'


def test_package_cache_with_mupifdb_registry(api, tmp_path):
    'An execution server gets packages from mupifDB through the cache: verified, extracted, prepared.'
    registry(api, 'admin@x').publish(makePackage(tmp_path / 'p'))
    reg = registry(api)
    ref = reg.resolve('my-model')
    path = PackageCache(tmp_path / 'cache').get(ref, reg.download, lambda d, m: None)
    assert (path / 'mymodel' / 'model.py').read_text() == 'VALUE = 1\n'


def test_command_line(api, tmp_path, capsys, monkeypatch):
    pkg = makePackage(tmp_path / 'p')
    assert mpk.main(['build', str(pkg), '-o', str(tmp_path / 'p.zip')]) == 0
    out = capsys.readouterr().out
    assert out.startswith('my-model@1.0 sha256:') and (tmp_path / 'p.zip').exists()
    cred = tmp_path / 'cred.json'
    cred.write_text(json.dumps({'username': 'admin@x', 'password': 'pw'}))
    monkeypatch.setenv('API_CREDENTIALS_FILE', str(cred))
    assert mpk.main(['--server', api.url, 'publish', str(tmp_path / 'p.zip')]) == 0
    assert 'Published my-model@1.0 sha256:' in capsys.readouterr().out
    assert mpk.main(['--server', api.url, 'show', 'my-model']) == 0
    assert json.loads(capsys.readouterr().out)['Version'] == '1.0'
    # published already: an error message (not a traceback), exit status 1
    assert mpk.main(['--server', api.url, 'publish', str(pkg)]) == 1
    out = capsys.readouterr().out
    assert out.startswith('Error:') and '409' in out
