"""
A fake ``apptainer`` executable for tests of :class:`mupif.launcher.ApptainerLauncher` and of
execution servers, without containers.

* ``pull --disable-cache <dest> <ref>`` -- writes ``<dest>`` (content ``fake image <ref>``); fails if
  the reference contains ``missing``;
* ``exec [--contain] [--cleanenv] [--nv] [--bind <spec>]... <sif> <python> <args>...`` -- runs the
  test interpreter with ``<args>`` (the image's interpreter is not used), with the environment a
  real ``apptainer exec --cleanenv`` gives: only the ``APPTAINERENV_*`` variables (prefix removed),
  ``PREPEND_PATH`` prepended to ``PATH``. ``/mupif/package`` in ``PYTHONPATH`` is replaced by the
  host directory bound there (no mount namespace here). The variable ``FAKE_APPTAINER_SIF`` tells
  the job which image it "runs in".

Every call is appended (JSON: the arguments) to ``calls.jsonl`` next to the fake executable.
"""

import os
import stat
import sys

SCRIPT = r'''#!{python}
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
with open(os.path.join(here, 'calls.jsonl'), 'a') as f:
    f.write(json.dumps(args) + '\n')
if args[0] == 'pull':
    assert args[1] == '--disable-cache', args
    dest, ref = args[2], args[3]
    if 'missing' in ref:
        sys.stderr.write('FATAL: failed to get image %s (fake)\n' % ref)
        sys.exit(255)
    with open(dest, 'w') as f:
        f.write('fake image ' + ref)
    sys.exit(0)
if args[0] != 'exec':
    sys.stderr.write('fake apptainer: unsupported command %r\n' % args)
    sys.exit(2)
i, binds = 1, {{}}
while args[i].startswith('-'):
    if args[i] == '--bind':
        parts = args[i + 1].split(':')
        binds[parts[1]] = parts[0]
        i += 2
    else:
        assert args[i] in ('--contain', '--cleanenv', '--nv'), args[i]
        i += 1
sif, python, rest = args[i], args[i + 1], args[i + 2:]
assert os.path.exists(sif), sif
env = {{k[len('APPTAINERENV_'):]: v for k, v in os.environ.items() if k.startswith('APPTAINERENV_')}}
pre = env.pop('PREPEND_PATH', '')
env['PATH'] = (pre + os.pathsep if pre else '') + '/usr/local/bin:/usr/bin:/bin'
if 'PYTHONPATH' in env:
    env['PYTHONPATH'] = os.pathsep.join(binds.get(p, p) for p in env['PYTHONPATH'].split(os.pathsep))
env['FAKE_APPTAINER_SIF'] = sif
os.execve({python!r}, [{python!r}] + rest, env)
'''


def install(directory) -> str:
    """Write the fake apptainer into *directory* and return its path."""
    path = os.path.join(str(directory), 'apptainer')
    with open(path, 'w') as f:
        f.write(SCRIPT.format(python=sys.executable))
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def calls(directory) -> list:
    """Return the calls of the fake installed in *directory* (lists of arguments)."""
    import json
    path = os.path.join(str(directory), 'calls.jsonl')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f]
