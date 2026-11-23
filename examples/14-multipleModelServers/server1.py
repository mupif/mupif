"""
The same mechanical demo model served under another name, ``example14.mechanical-alt``.

Its registration carries the same ``ModelID:Mechanical-1`` tag as the servers of ``server.py``, so a
workflow model giving ``ModelID: Mechanical-1`` may run on either.
"""
import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

mp.ModelServer(
    ns=mp.pyroutil.connectNameserver(),
    appClass=mp.demo.MechanicalModel,
    appName='example14.mechanical-alt',
    maxJobs=1,
).runServer()
