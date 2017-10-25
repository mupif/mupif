MuPIF: Multi-Physics Integration Framework 
==========================================

Multi-Physics Integration Framework [MuPIF](http://mupif.org) is an integration framework, that 
will facilitate the implementation of multi-physics and multi-level simulations,
built from independently developed components. The principal role of the
framework is to steer individual components (applications) and to provide 
high-level data-exchange services. Each application should implement 
an interface that allows to steer application and execute data requests. 
The design supports various coupling strategies, discretization techniques, 
and also the distributed applications. 

MuPIF has been developped at Czech Technical University by Borek Patzak and coworkers and is available under GNU Library or Lesser General Public License version 3.0 (LGPLv3).

Getting Started
===============

MuPIF is distributed as a module with the following directory tree structure:
    MuPIF_TOP_DIR - contains source code and other files of the MuPIF package
       +--mupif - contains source code of the MuPIF package
       |    +--doc - documentation (reference manual and User guide)
       |    +--examples - examples and tests
       |    +--Physics - module for units
       |    +--tools - various supportive tools
       |    +--tests - tests for nosetests module 
       |    +--*.py - MuPIF classes
       |    +--__init__.py - description of MuPIF module
       +--LICENSE.txt - LGPL license conditions
       +--MANIFEST.in - support for setuptools
       +--README.txt - general description
       +--setup.py - support for setuptools, Pypi upload etc.



Prerequisites
=============

MuPIF requires the python interpreter, version 3.2 or newer. It has been tested on Linux / Windows systems. Network communication relies on Pyro4 module.

Installing
----------

There are two options for MuPIF installation. The first one relies on Python Package Index (run as pip3 or pip) which is installed via
*pip3 install mupif* systemwide, needing root priviledges or
*pip3 install mupif --user* as a user

To uninstall, run 
*pip3 uninstall mupif*

The second option relies on the most advanced version on github
*git clone https://github.com/mupif/mupif.git mupif.git*

mupif.fast
----------

Some operations in mupif can be accelerated by using compiled modules. All such features will be enabled automatically if detected, no user interaction is necessary. They are collectivelly called ``mupif.fast``.

1. [minieigen](https://pypi.python.org/pypi/minieigen) module will be used for faster bounding-box implementation. 

2. Experimental ``mupif.fastOctant`` will be compiled if ``useCxx=True`` is manually set in ``setup.py`` (Linux-only). The compilation requires ``boost_python`` and [Eigen](http://eigen.tuxfamily.org>); runtime requires minieigen as in the previous point.

Running the tests
=================

Run *nosetests3* anywhere in MuPIF source tree to check basic functionality. Add *--verbose* for verbose output and, if you have *rednose* installed, add *--rednose* for prettier output.

Subdirectory *examples* contains more advanced examples for MuPIF testing. They start with a simple test on a local computer and continue through demonstrating network communication and job manager functionality. It is possible to run tests on a single computer or in distributed manner using ssh tunnels or VPN. The tests also contain stationary and nonstationary thermo-mechanical linked simulations with VTK output. Consult README files in individual directories for instructions.

Bugs
====

Please mail all bug reports and suggestions to mailto:info@oofem.org. I will try to give satisfaction, if the time is at least partially on my side. 

Versioning
==========

For the versions available, see the [git repository](https://github.com/mupif/mupif.git).
or [pip archive](https://pypi.python.org/pypi/mupif).

Authors
=======

Bořek Patzák
Vít Šmilauer
Václav Šmilauer
Martin Horák
Guillaume Pacquaut

License
=======

MuPIF is available under GNU Library or Lesser General Public License version 3.0 (LGPLv3) 

Acknowledgements
================

The MuPIF development has been supported by Grant Agency of the Czech Republic 
(Project No. P105/10/1402), by EU under 7th Framework programme (MMP project,
Grant agreement no: 604279) and by Horizon 2020 programme (Composelector project, Project reference: 721105).

