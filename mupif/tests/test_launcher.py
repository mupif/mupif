"""Tests of :mod:`mupif.launcher`: command lines and environments of job processes."""

import os
import sys

from mupif.launcher import Launcher, LocalPythonLauncher


BOOTSTRAP = ['-c', 'import mupif; mupif.ModelServer._spawnedProcessPopen()', '-', b'pickled']


def test_local_python_command_uses_server_interpreter():
    assert LocalPythonLauncher().command(BOOTSTRAP) == [sys.executable, *BOOTSTRAP]


def test_local_python_env_puts_sys_path_before_inherited_pythonpath():
    env = LocalPythonLauncher(pythonPath=['/pkg']).env({'PYTHONPATH': '/inherited', 'X': '1'})
    parts = env['PYTHONPATH'].split(os.pathsep)
    # package directory first, then the server's sys.path, the inherited PYTHONPATH last
    assert parts[0] == '/pkg' and parts[-1] == '/inherited'
    assert parts[1:-1] == list(sys.path)
    assert env['X'] == '1'


def test_local_python_env_without_inherited_pythonpath():
    env = LocalPythonLauncher().env({})
    assert env['PYTHONPATH'] == os.pathsep.join(sys.path)


def test_extra_env_and_path():
    base = {'PATH': '/usr/bin', 'LM_LICENSE_FILE': 'old'}
    env = Launcher(extraEnv={'LM_LICENSE_FILE': '27000@lic'}, extraPath=['/opt/a/bin', '/opt/b/bin']).env(base)
    assert env['PATH'] == os.pathsep.join(['/opt/a/bin', '/opt/b/bin', '/usr/bin'])
    assert env['LM_LICENSE_FILE'] == '27000@lic'
    # the base environment is not changed
    assert base == {'PATH': '/usr/bin', 'LM_LICENSE_FILE': 'old'}


def test_extra_path_without_inherited_path():
    assert Launcher(extraPath=['/opt/a/bin']).env({})['PATH'] == '/opt/a/bin'
