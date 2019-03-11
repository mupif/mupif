"""
Created 19.6.2015
@author: Vit Smilauer
"""

# A typical workflow
# $ python3 setup.py install --user   test your installation locally as a user, installs under /home/user/.local/lib/
# $ python3 setup.py install       test your installation locally as a root as it would be downloaded from PyPI server
# $ python3 setup.py sdist         creates an archive on a local computer
# $ python3 setup.py sdist --format=zip creates source archive on local computer

# UPLOAD
# python3 setup.py sdist         creates an archive on a local computer
# twine upload dist/*            uploads to pypi.python.org, needs .pypirc config file

# The mupif module can be tested under python $ python   and  >> from mupif import * .
# Correct path is automatically added.
# Uninstall with $ pip uninstall mupif . This also shows you the location of files.

# Alternatively, without default path, $ pip install --user dist/mupif-0.1.tar.gz
# See also https://bashelton.com/2009/04/setuptools-tutorial/#setup.py-package_dir
# See also https://docs.python.org/2/distutils/setupscript.html

import sys
import re

from setuptools import setup, find_packages

version = ['']
author = ['']

inFile = open("mupif/__init__.py")
for line in inFile:
    if line.startswith('__version__'):
        # version = line.split()[2]
        version = re.findall(r'\'(.+?)\'', line)
    # print version[0]
    elif line.startswith('__author__'):
        author = re.findall(r'\'(.+?)\'', line)
        # print author[0]
inFile.close()


# enable useCxx to use experimental and optional mupif.fastOctant module (Linux-only)
useCxx = False

# punish those running Windows (wouldn't work anyway)
if useCxx and sys.platform == 'win32':
    raise RuntimeError('useCxx is not supported under Windows.')

if not useCxx:
    ext_modules = []
else:
    from setuptools import Extension
    ext_modules = [Extension('mupif.fastOctant', sources=['mupif/fastOctant.cpp'], libraries=['boost_python-py%d%d' % (
        sys.version_info[0], sys.version_info[1])], include_dirs=['/usr/include/eigen3'], define_macros=[],
                             extra_compile_args=['-std=c++11'])]


setup(
    name='mupif',
    version=version[0],
    description='MuPIF platform for multiscale/multiphysics modeling',
    long_description=open('README.txt', 'r').read(),
    license='LGPL',
    author=author[0],
    author_email='info@oofem.org',
    # package_dir={'': 'mupif'},#this looks where to find __init__.py
    packages=find_packages(),
    # packages = ['mupif'],
    # Tell what to install (these files must be already in a sdist archive file) - package_data useful only for bdist,
    # not for pip. Extra added files are in MANIFEST.in
    # package_data={'': [ 'README', '*.sh', '*.c', '*.in', 'tools/*.py', 'examples/Ex*/*.py', 'examples/Pi*/*.py',
    # 'examples/Workshop02/*.py', 'doc/refManual/MuPIF.pdf', 'doc/userGuide/MuPIF-userGuide.pdf' ]},
    # 'scipy' fails due to missing compiler for Lapack etc.
    install_requires=[
        'numpy', 'scipy', 'setuptools', 'enum34', 'pyvtk', 'config', 'nose', 'rednose', 'Pyro4==4.74', 'jsonpickle',
        'jsonschema', 'vtk', 'matplotlib'
    ],
    include_package_data=True,
    url='http://www.mupif.org/',
    entry_points={
        'console_scripts': [
            'jobMan2cmd = mupif.tools.JobMan2cmd:main',
            'jobManStatus = mupif.tools.jobManStatus:main',
            'jobManTest = mupif.tools.jobManTest:main',
            'startMupifNameserver = mupif.tools.nameserver:main'
        ]
    },
    ext_modules=ext_modules,
)
