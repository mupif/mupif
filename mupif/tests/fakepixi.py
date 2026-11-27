"""
A fake ``pixi`` executable for tests of launchers and execution servers, without network or pixi.

It understands the two commands :class:`mupif.launcher.PixiLauncher` uses:

* ``install --locked -e <env> --manifest-path <pkg>/pixi.toml`` -- "installs" the environment
  ``<pkg>/.pixi/envs/<env>``: its ``bin/python`` is a wrapper running the test interpreter (so that
  jobs can import mupif and its dependencies). Fails if the package contains a file ``FAIL``. Every
  call is appended to ``<pkg>/.pixi/install-calls``.
* ``shell-hook --json --locked -e <env> --manifest-path …`` -- prints the activation: ``CONDA_PREFIX``,
  ``PATH`` and ``FAKE_PIXI_ACTIVATED=<env>``.
"""

import os
import stat
import sys

SCRIPT = r'''#!{python}
import json, os, sys
args = sys.argv[1:]
manifest = args[args.index('--manifest-path') + 1]
envName = args[args.index('-e') + 1]
assert '--locked' in args, 'PixiLauncher must always use --locked'
pkg = os.path.dirname(os.path.abspath(manifest))
prefix = os.path.join(pkg, '.pixi', 'envs', envName)
if args[0] == 'install':
    os.makedirs(os.path.join(pkg, '.pixi'), exist_ok=True)
    with open(os.path.join(pkg, '.pixi', 'install-calls'), 'a') as f:
        f.write(' '.join(args) + '\n')
    if os.path.exists(os.path.join(pkg, 'FAIL')):
        sys.stderr.write('Error: failed to solve the environment (fake)\n')
        sys.exit(1)
    os.makedirs(os.path.join(prefix, 'bin'), exist_ok=True)
    py = os.path.join(prefix, 'bin', 'python')
    with open(py, 'w') as f:
        f.write('#!/bin/sh\nexec {python} "$@"\n')
    os.chmod(py, 0o755)
elif args[0] == 'shell-hook':
    print(json.dumps({{'environment_variables': {{
        'CONDA_PREFIX': prefix,
        'PATH': os.path.join(prefix, 'bin') + os.pathsep + os.environ.get('PATH', ''),
        'FAKE_PIXI_ACTIVATED': envName,
    }}}}))
else:
    sys.stderr.write('fake pixi: unsupported command %r\n' % args)
    sys.exit(2)
'''


def install(directory) -> str:
    """Write the fake pixi into *directory* and return its path."""
    path = os.path.join(str(directory), 'pixi')
    with open(path, 'w') as f:
        f.write(SCRIPT.format(python=sys.executable))
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path
