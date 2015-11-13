
MuPIF: Multi-Physics Integration Framework 
==========================================

[![Build Status](https://travis-ci.org/mmp-project/mupif.svg?branch=master)](https://travis-ci.org/mmp-project/mupif)


Description
------------

Multi-Physics Integration Framework (MuPIF) is an integration framework, that 
will facilitate the implementation of multi-physic and multi-level simulations,
built from independently developed components. The principal role of the
framework is to steer individual components (applications) and to provide 
high-level data-exchange services. Each application should implement 
an interface that allows to steer application and execute data requests. 
The design supports various coupling strategies, discretization techniques, 
and also the distributed applications. 

The MuPIF development has been supported by Grant Agency of the Czech Republic 
(Project No. P105/10/1402) and by 7FP EU Framework programme (MMP project,
Grant agreement no: 604279).

What is here
-------------

The directory tree below holds source code to the MuPIF package plus supportive
files::

    MuPIF_TOP_DIR - contains source code and other files of the MuPIF package
       +--mupif - contains source code of the MuPIF package
       |    +--doc - documentation (reference manual and User guide)
       |    +--examples - examples and tests
       |    +--Physics - module for units
       |    +--tools - various supportive tools
       |    +--*.py - MuPIF classes
       |    +--__init__.py - description of MuPIF module
       +--README.txt - general description
       +--setup.py - support for setuptools
       +--MANIFEST.in - support for setuptools


Pre-requisites
---------------
The MuPIF requires the python interpreter.
Some examples rely on vtk python module which requires Python 2.x version.

MuPIF depends on application interfaces, which typically require that 
corresponding package is installed properly. 
To support parallel and distributed simulation scenarios, MuPIF requires Pyro
module.

Running MuPIF examples
-----------------------

Please read README files in individual example directories for instructions.

Installation
-------------
Use ``$ pip install mupif`` to install mupif as a package from PyPI. Use ``$ git clone git://git.code.sf.net/p/mupif/code mupif.git``  to get a git 
version.

To build an installable MuPIF package, several options are available.
A package setuptools is normally used for creating e.g. installable tar files.
Simply run a command $python setup.py sdist  to create ``sdist/*.tar.gz`` file.

``$ python setup.py install`` installs the MuPIF on local disk - need a root 
priviledges by default. To uninstall, use ``$ pip freeze``  and then something like
``$ pip uninstall mupif``.


### mupif.fast
Some operations in mupif can be accelerated by using compiled modules. All such features will be enabled automatically if detected, no user interaction is necessary. They are collectivelly called ``mupif.fast``.

1. [minieigen](https://pypi.python.org/pypi/minieigen) module will be used for faster bounding-box implementation. 

2. Experimental ``mupif.fastOctant`` will be compiled if ``useCxx=True`` is manually set in ``setup.py`` (Linux-only). The compilation requires ``boost_python`` and [Eigen](http://eigen.tuxfamily.org>); runtime requires minieigen as in the previous point.


Bugs
-----

Please mail all bug reports and suggestions to mailto:info@oofem.org. I will try to give satisfaction, if the time is at least partially on my side. 


Legal notice
------------

                Copyright (C) 2010-2014 Borek Patzak

       Czech Technical University, Faculty of Civil Engineering,
    Department of Structural Mechanics, 166 29 Prague, Czech Republic

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

