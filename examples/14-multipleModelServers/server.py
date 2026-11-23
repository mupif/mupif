"""
Model server of the mechanical demo model, registered as ``example14.mechanical``.

Run it several times to get several instances of the same model server: the first one registers
under the base name, the others (while the first one runs) as ``example14.mechanical~<host>-<pid>``.
Give an instance id as the first argument (or in ``MUPIF_MODELSERVER_INSTANCE``) to choose the
instance name: ``python server.py node2`` registers ``example14.mechanical~node2``.
"""
import sys
sys.path += ['..', '../..']
import mupif as mp
import mupif.demo

mp.ModelServer(
    ns=mp.pyroutil.connectNameserver(),
    appClass=mp.demo.MechanicalModel,
    appName='example14.mechanical',
    instance=(sys.argv[1] if len(sys.argv) > 1 else None),
    maxJobs=1,
).runServer()
