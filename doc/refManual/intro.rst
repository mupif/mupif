Introduction
=============

Multi-Physics Integration Framework (MuPIF) is an integration framework, that will facilitate the implementation of multi-physic and multi-level simulations, built from independently developed components. The principal role of the framework is to steer individual components (applications) and to provide high-level data-exchange services. Each application should implement an interface that allows to steer application and execute data requests. The design supports various coupling strategies, discretization techniques, and also the distributed applications. The platform development is hosted on GitHub (https://github.com/mupif/mupif/).


The approach followed in this project is based on an object-oriented approach,
consisting in designing a system of interacting objects for the purpose of solving a
software problem. The identification of individual objects and their mutual interaction has
been based on expertise of project partners, and later refined by analysis of simulation
scenarios considered in the project. The main advantage of this approach lies in
independence on particular data format(s), as the exchanged data (fields, properties) are
represented as abstract classes. Therefore, the focus on services is provided by objects
(object interfaces) and not on underlying data itself.

The integration framework is implemented in Python3. Python is an interpreted,
interactive, object-oriented programming language. It runs on many Unix/Linux
platforms, on the Mac, and on PCs under MS-DOS, Windows, Windows NT, and OS/2.
The Python language is enriched by new objects/classes to describe and to
represent complex simulation chains. Such approach allows profiting from the
capabilities of established scripting environment, including numerical libraries,
serialization/persistence support, VPN, and remote communication.

The proposed abstract classes are designed to represent the entities in a model space,
including simulation tools, fields, discretizations, properties, etc. The purpose of these
abstract classes is to define a common interface that needs to be implemented by any
derived class. Such interface concept allows using any derived class on a very abstract
level, using common interface for services, without being concerned with the
implementation details of an individual software component.

To facilitate execution and development of the simulation workflows, the platform provides the transparent communication mechanism that will take care of the network communication between the objects. An important feature is the transparency, which hides the details of remote communication to the user and allows working with local and remote objects in the same way. The communication layer is built on Pyro4 library, which provides a transparent distributed object system fully integrated into Python. It takes care of the network communication between the objects when they are distributed over different machines on the network. The platform is designed to work on virtually any distributed platform, including grid and cloud infrastructure. 

In addition to this MuPIF reference manual, a user manual from https://github.com/mupif/mupif/tree/master/mupif/doc/userManual can be obtained, showing details on API implementation, installation, networking and providing several examples in local/distributed setups.