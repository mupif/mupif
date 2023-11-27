Reference documentation
========================

MuPIF classes are organized in a hierarchy, which is briefly described here:

.. mermaid::
   
   graph TD;
      mupif.ObjectBase-->BareData
      WithMetadata-->Data
      BareData-->Data
      mupif.ObjectBase-->Process
      mupif.ObjectBase-->Utility
      WithMetadata-->Process

**mupif.Object**
   Defines attribute handling and validation (e.g. keywords passed to constructor are assigned to attributes)
**WithMetadata**
   Adds metadata to each instance
**BareData**
   Adds RPC capabilities (Pyro) and serialization (Pyro, JSON, ...)
**Data**
   Data with metadata
**Process**
   Objects standing for processes, such as Model and Workflow
**Utility**
   Other objects which don't fit anywhere else; typically proxy classes such as :ref:`PyroFile` or `RefQuantity`


.. automodule:: mupif
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
