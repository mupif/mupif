Development notes
====================

Testing under Wine
-------------------

The `wenv <https://pypi.org/project/wenv/>`__ can be used for testing MuPIF operation on the Windows platform under Linux.

Several depencies are compiled for amd64 only, thus wine platform must be set to ``win64`` in wenv's config file (e.g. ``~/.wenv.json`` or elsewhere, as documented)::

    {"arch":"win64"}

The whole installation is the relatively simple:

.. code-block: bash

   pip install wenv
   wenv init
   wenv pip install --only-binary=vtk --only-binary=h5py --only-binary=pyrsistent -r requirements.txt

The last line prevents compilation of complex packages from the source (binaries are available).

After that, the test suite can be run as::

   MUPIF_PYRO5=1 wenv nosetests --rednose

TODO
-----

* rename packages to follow `PEP8 <https://pep8.org/>`__.
* make Pyro5 default (rather than opt-in with ``MUPIF_PYRO5`` env var)
