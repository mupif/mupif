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

:obj:`~mupif.ObjectBase`
   Defines attribute handling and validation (e.g. keywords passed to constructor are assigned to attributes)
:obj:`~mupif.WithMetadata`
   Adds metadata to each instance
:obj:`~mupif.BareData`
   Adds RPC capabilities (Pyro) and serialization (Pyro, JSON, ...)
:obj:`~mupif.Data`
   Data with metadata
:obj:`~mupif.Process`
   Objects standing for processes, such as Model and Workflow
:obj:`~mupif.Utility`
   Other objects which don't fit anywhere else; typically proxy classes such as :obj:`mupif.PyroFile` or :obj:`mupif.RefQuantity`


.. automodule:: mupif
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
   :exclude-members: __init__,Config,construct,__str__,copy,dict,from_orm,json,parse_file,parse_obj,parse_raw,schema,schema_json,update_forward_refs,validate,preDumpHook,metadata,isInstance,hasMetadata,getMetadata,getAllMetadata,deepcopy,printMetadata,setMetadata,updateMetadata,validateMetadata,toJSON,toJSONFile,dumpToLocalFile,from_dict,from_dict_with_name,copyRemote,to_dict,loadFromLocalFile
