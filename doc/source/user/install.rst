.. _sect-platform-installation:

Platform installation
========================

Prerequisites
------------------

MuPIF installatoin requires:

* Python ≥ 3.8

  * Windows: we suggest to install `Anaconda scientific python package <https://store.continuum.io/cshop/anaconda/>`__, which includes Python ≥ 3.8;
  * Linux: use system-installed Python (if ≥ 3.8) or install a separate interpreter via Anaconda;

* Wireguard (VPN software): see `Wireguard Installation <https://www.wireguard.com/install>`__.

* git version control system, as MuPIF itself it pulled from its git repository directly (Linux: install package `git`; Windows: `Git Downloads for Windows <https://git-scm.com/download/win>`__)

Local installation
----------------------

Full source
~~~~~~~~~~~~~

This is the recommended installation method. One can run examples and tests and the complete source code is stored on your computer. 
First clone the remote repository to your computer with (replace ``BRANCH_NAME`` with project-specific branch such as ``Musicode`` or ``Deema``; see `MuPIF branches at GitHub <https://github.com/mupif/mupif/branches>`__)::

   git clone --branch BRANCH_NAME https://github.com/mupif/mupif.git

and then run inside the repository::

   pip install -e .

You can run ``git pull`` in the cloned repository to update your installation.

Modules only
~~~~~~~~~~~~~

Run the following command (it can be re-run later for pulling the latest revision)::

   pip install --upgrade git+https://github.com/mupif/mupif.git@BRANCH_NAME


Other recommended packages/softwares
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Paraview (tested >=5.0), visualization application for vtu data
   files, `http://www.paraview.org/`.

-  Windows: Notepad++ (tested 6.6.9),
   `http://notepad-plus-plus.org/`

-  Windows: conEmu, windows terminal emulator,
   `https://code.google.com/p/conemu-maximus5/`.

Test and examples
-------------------

Unit tests
~~~~~~~~~~~

MuPIF platform comes with unit tests. To run unit tests, you need the pytest module::

   pip install pytest

Then from the top-level MuPIF repository directory, execute::

   pytest-3

You should see output something like this::

   $ pytest-3 
   ============================================================= test session starts ==============================================================
   platform linux -- Python 3.10.2, pytest-6.2.5, py-1.10.0, pluggy-0.13.0
   rootdir: /home/eudoxos/build/mupif
   plugins: cov-3.0.0
   collected 144 items                                                                                                                            

   mupif/tests/test_BBox.py ......                                                                                                          [  4%]
   mupif/tests/test_Cell.py ..................................                                                                              [ 27%]
   mupif/tests/test_Field.py ...............                                                                                                [ 38%]
   mupif/tests/test_IntegrationRule.py ..                                                                                                   [ 39%]
   mupif/tests/test_Mesh.py ............                                                                                                    [ 47%]
   mupif/tests/test_Metadata.py ....                                                                                                        [ 50%]
   mupif/tests/test_Particle.py ..........                                                                                                  [ 57%]
   mupif/tests/test_ModelServer.py .......                                                                                                  [ 62%]
   mupif/tests/test_TimeStep.py ....                                                                                                        [ 65%]
   mupif/tests/test_Vertex.py ....                                                                                                          [ 68%]
   mupif/tests/test_VtkReader2.py s                                                                                                         [ 68%]
   mupif/tests/test_app.py .                                                                                                                [ 69%]
   mupif/tests/test_heavydata.py ..........................                                                                                 [ 87%]
   mupif/tests/test_multipiecelinfunction.py .                                                                                              [ 88%]
   mupif/tests/test_property.py ......                                                                                                      [ 92%]
   mupif/tests/test_pyro.py ......                                                                                                          [ 96%]
   mupif/tests/test_saveload.py s...                                                                                                        [ 99%]
   mupif/tests/test_units.py .                                                                                                              [100%]

   ======================================================= 142 passed, 2 skipped in 10.34s ========================================================

Indicating that *pytest* found and ran listed tests successfully.

Running examples
~~~~~~~~~~~~~~~~~~~

In addition, the platform installation comes with many examples, that
can be used to verify the successful installation as well, but they primarily 
serve as an educational examples illustrating the use of the platform. The exmaples are located in examples subdirectory of your MuPIF installation and also are accessible directly from GitHub `https://github.com/mupif/mupif/tree/master/examples`.

To run the examples, go the the examples directory and use the ``runex.py`` script to do the set-up and run the example::

  cd examples
  python3 runex.py       # run all examples
  python3 runex.py 1 4 5 # run some examples

MuPIF Basic Infrastructure
---------------------------

MuPIF can be run on a single workstation serving the infrastructure locally. However, to take a full profit from its distributed design, a supporting infrastructure has to be set up.
This typically includes setting up of VPN network to isolate and secure comminication and data exchange. 
There are additional services, including nameserver for service discovery and scheduler for job scheduling. They are described in subsequent chapters.
The following chapters describe these resources from user perspective. The administrative prespective, including set up instrauctions is described in `sect-distributed-model`_.

Wireguard VPN
~~~~~~~~~~~~~~

Integrating the local computer into the already set-up VPN requires a configuration file (to be received over a secure channel) for Wireguard. This is documented in `sect-vpn-setup`_.


.. _sect-nameserver:

Nameserver
~~~~~~~~~~~~~~

In order to let MuPIF know which existing connected infractructure to use, the nameserver connection details are needed. They consist of nameserver IP address and port. By default, the VPN IP adress of nameserver is `172.22.2.1` and port is 10000. You should receive details from platform admin.
The nameserver IP address and port determine so called address:port string, so for example, it corresponds to ``172.22.2.1:10000``; for IPv6, additionally enclose the address in braces, e.g. ``[fd4e:6fb7:b3af:0000::1]:10000``.

The address:port string should be then stored either in the environment variable ``MUPIF_NS`` or in the file ``MUPIF_NS`` in user-config directory (``~/.config/MUPIF_NS`` in Linux, ``C:\Users\<User>\AppData\Local\MUPIF_NS`` in Windows (probably)).
This will ensure that your MuPIF installation will talk to the correct nameserver when it runs.

You can re-run the examples once ``MUPIF_NS`` is set and you should see MuPIF running the examples using the VPNs nameserver.

