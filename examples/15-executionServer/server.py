"""
Execution server of example 15: runs any model package of its registry on demand.

The registry is mupifDB if ``MUPIFDB_REST_SERVER`` is set (publish the package there first:
``python -m mupif.modelpackage publish model-package``; the account is in ``API_CREDENTIALS_FILE``),
else the package directory next to this script (no database needed).

Packages and their environments are cached in ``cache/`` here (``MUPIF_EXAMPLE15_CACHE`` to change
it): the first job of the model downloads the package and installs its pixi environment, which takes
a while; the following ones start at once. pixi must be installed (``PATH``, ``~/.pixi/bin``, or
``PIXI_EXE``).
"""
import os
import sys
d = os.path.dirname(os.path.abspath(__file__))
sys.path += [d+'/../..']
import mupif as mp
from mupif.modelpackage import DirectoryRegistry

if os.environ.get('MUPIFDB_REST_SERVER'):
    from mupif.mupifdbclient import MupifDBRegistry
    registry = MupifDBRegistry()
else:
    registry = DirectoryRegistry(os.path.join(d, 'model-package'))

ns = mp.pyroutil.connectNameserver()
mp.ExecutionServer(
    ns=ns,
    appName='mupif/example15/exec',
    registry=registry,
    cacheDir=os.environ.get('MUPIF_EXAMPLE15_CACHE', os.path.join(d, 'cache')),
    maxJobs=2,
).runServer()
