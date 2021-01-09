ChangeLog
=============

Version 1.1 (05/2017)
---------------------------

-  Expanded section on workflow implementation, added subsections on
   workflow templates and workflow as a class. Already describes some
   concept to be introduced in ver. 2.0 (transparent ssh tunnel handling
   using decorator classes).

-  Added acknowledgement to EU Composelector project.

Version 2.0.0 (12/2017)
-----------------------------

-  Updated API doc to MuPIF ver. 2.0

-  Metadata support by introducing abstract, top-level *MuPIFObject*
   class, which is a parent class to all MuPIF components and provides
   methods to attach and retrieve metadata

-  Workflows can be represented as a class derived from *Workflow*
   class. Workflows share the same API as models (*Model* class). This
   allows to combine models and workflows and create a complex,
   hierarchical workflows. Several examples converted to demonstrate
   workflow-as-a-class concept.

-  TimeStep now requires unit information on all attributes, introduced
   new attribute allowing to set target simulation time.

-  Base *Property* class generalized to allow for properties depending
   on parameters (time, other variables), Properties now strictly unit
   aware.

-  *Field* class now strictly unit aware.

-  Added section on VPN online monitoring tool

Version 2.2.0 (04/2019)
-----------------------------

-  Updated to MuPIF ver 2.2

-  Updated to Python ≥ 3.2

-  Section 5.1 extended to cover metadata and metadata schemata

-  Updated example numbering

-  Updated Pyro4 to version 4.75

Version 2.3.0 (02/2020)
-----------------------------

-  Updated to MuPIF ver 2.3

-  Updated to Python ≥ 3.5

-  Added Particle and ParticleSet classes and corresponding unit tests

-  Fixing metadata schemas for Model and Workflow classes

-  Email notification of failed JobManager

-  Fixing Mesh class for vertex support

-  Pilot tests for EMMO (European Materials & Modelling Ontology) under
   examples/Example06-stacTM-local/emmo*.py


