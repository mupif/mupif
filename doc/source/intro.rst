Introduction
=============
MuPIF is a modular, object-oriented integration platform allowing to create and execute complex, 
distributed, multi physics simulation workflows across the scales and processing chains by 
combining existing simulation tools. MuPIF is written in Python language and is distributed under LGPL license.

The approach followed in MuPIF is based on a system of distributed, interacting components 
designed to represent simulation workflow. The individual components represent, for example, 
instances of individual models or data types. Following object-oriented design, 
the abstract classes are introduced to represent a particular kind of components, 
defining standardized interfaces allowing to manipulate individual instances using generic, 
abstract interface. Such interface concept allows using any derived class on a very abstract level, 
using standardized interface, without being concerned with the implementation details of an 
individual component. This allows, for example, to operate all models using generic interface. 
Moreover, as the simulation data are represented as components as well, the similar design
pattern allowing to manipulate data of the same type using standardized interfaces is applied,
making the platform independent on data format(s). The models exchange the component representation 
of data, consisting of raw data and operations, this way the models know how to interpret the data transparently. 
Therefore, the focus is on services provided by components and not on underlying data itself. 
In this way, the MuPIF platform is not standardizing the structure of data, it is standardizing the fundamental, core operations on the data. 

MuPIF by design supports distributed workflows, taking advantage of workflow execution on distributed computational resources including HPCs.
The platform provides the transparent communication mechanism that will take care of the network communication between the objects. 

MuPIF comes with a Data Management System (DMS) called MuPIFDB. 
The DMS is used to track integrated simulation workflows, their executions including execution inputs and outputs.
It also provides a generic Digital Twin model, which is based on Entity Data Model (EDM). The EDM identifies the individual entities, 
their attributes and relations between them. The EDM is defined using JSON schema, and the DMS structure is generated from this schema.
The EDM allows to map entity attributes to simulation workflow inputs (determining the initial conditions) and simulation workflow outputs 
can be mapped to newly cloned entities representing updated configuration(s). The EDM can be regarded as hypergraph, 
where nodes represent entity states and edges representing processes.
At the same time, MuPIF can interface to 3rd party DMS via its generic foreign DMS interface layer. 

