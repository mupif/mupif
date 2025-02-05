# MuPIF

MuPIF platform is an open-source, modular, and object-oriented simulation platform designed to create complex, distributed, multiphysics simulation workflows. It integrates existing simulation tools to handle various scales and processing chains.

Key features of MuPIF include:

* Distributed Design: Allows execution of simulation scenarios involving remote applications and data.
* Data Management System (DMS): Builds digital twin representations of physical systems, enhancing predictive simulations.
* Interoperability: Standardizes application and data component interfaces, enabling seamless integration of different simulation models and data types.
* Graphical Workflow Editor: Facilitates low-code workflow development and makes implementation more accessible.
* Security: Supports SSL or VPN-based secure communication and data exchange.

MuPIF is written in Python and can be used on various operating systems, making it a versatile tool for researchers and engineers.
 
[![Build Status](https://travis-ci.org/mupif/mupif.svg?branch=master)](https://travis-ci.org/mupif/mupif)
[![codecov](https://codecov.io/gh/mupif/mupif/branch/master/graph/badge.svg)](https://codecov.io/gh/mupif/mupif)
[![PyPI version](https://badge.fury.io/py/mupif.svg)](https://badge.fury.io/py/mupif)
[![Downloads](https://pepy.tech/badge/mupif)](https://pepy.tech/project/mupif)
[![Downloads](https://pepy.tech/badge/mupif/month)](https://pepy.tech/project/mupif)

## Documentation
* [User manual and reference](https://mupif.readthedocs.io/en/latest)
* [MuPIF homepage](http://www.mupif.org)

## Prerequisites
MuPIF requires the python interpreter, version 3.8 or newer. It has been tested on Linux / Windows systems. Network communication relies on Pyro5 module.

## Installation

There are two options for MuPIF installation:
* The first, recommended one, relies on Python Package Index (run as pip3 or pip) 
* For a system wide installation (needs admin privileges): `pip3 install --upgrade git+https://github.com/mupif/mupif.git`
* For a user space installation: `pip3 install mupif --user`

The second option relies on the most advanced version on github:
* ```git clone https://github.com/mupif/mupif.git mupif.git```

## License
MuPIF has been developed at Czech Technical University by Borek Patzak and coworkers and is available under GNU Library or Lesser General Public License version 3.0 (LGPLv3).

## Further information
Please consult MuPIF home page (http://www.mupif.org) for additional information.
