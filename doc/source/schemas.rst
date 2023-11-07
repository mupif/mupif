.. _sect-schemas-doc:

Schemas
#######

Schema documentation is hosted externally, please follow these links:

* `Model metadata <https://json-schema-viewer.vercel.app/view?https%3A%2F%2Freadthedocs.io%2F_static%2Fschema%2FModelMeta.json&expand_buttons=on&show_breadcrumbs=on>`__
* `Workflow metadata <https://json-schema-viewer.vercel.app/view?https%3A%2F%2Freadthedocs.io%2F_static%2Fschema%2FModelMeta.json&expand_buttons=on&show_breadcrumbs=on>`__
* `HeavyStruct <https://json-schema-viewer.vercel.app/view?https%3A%2F%2Freadthedocs.io%2F_static%2Fschema%2FModelMeta.json&expand_buttons=on&show_breadcrumbs=on>`__


Legacy
========

Workflow and Model
-------------------

.. autopydantic_model:: mupif.meta.ModelWorkflowCommonMeta
   :undoc-members:

.. autopydantic_model:: mupif.meta.ModelMeta
   :undoc-members:

.. autopydantic_model:: mupif.meta.WorkflowMeta
   :undoc-members:

Nested models
""""""""""""""

.. automodule:: mupif.meta
   :members:
   :undoc-members:
   :exclude-members: ModelWorkflowCommonMeta,ModelMeta,WorkflowMeta


HeavyStruct
------------

.. jsonschema:: mupif.heavystruct.HeavyStructSchemaModel
   :lift_title: false
