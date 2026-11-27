"""
Execution server of example 16: runs model packages in Apptainer containers.

Builds the package first if needed (make_package.py: the image, then package/). The registry is
mupifDB if ``MUPIFDB_REST_SERVER`` is set (publish the package first:
``python -m mupif.modelpackage publish package``), else ``package/`` itself. The image is copied into
the package cache (``cache/``, or ``MUPIF_EXAMPLE16_CACHE``) and verified on the first job.
"""
import os
import sys
d = os.path.dirname(os.path.abspath(__file__))
sys.path += [d, d+'/../..']
import mupif as mp
from mupif.modelpackage import DirectoryRegistry
import make_package

packageDir = make_package.build()
if os.environ.get('MUPIFDB_REST_SERVER'):
    from mupif.mupifdbclient import MupifDBRegistry
    registry = MupifDBRegistry()
else:
    registry = DirectoryRegistry(packageDir)

ns = mp.pyroutil.connectNameserver()
mp.ExecutionServer(
    ns=ns,
    appName='mupif/example16/exec',
    registry=registry,
    cacheDir=os.environ.get('MUPIF_EXAMPLE16_CACHE', os.path.join(d, 'cache')),
    runtimes=['apptainer'],
    maxJobs=2,
).runServer()
