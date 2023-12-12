User manual
###############


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

MuPIF resources
===========================

- `MuPIF project web page  <https://mupif.org/>`__
- `MuPIF github repository <https://github.com/mupif/mupif.git>`__
- `Online User manual and Reference manual <https://mupif.readthedocs.io/en/latest/#>`__ (this document)
- The Musicode project MuPIF training video recordings are available on YouTube: `Musicode MuPIF training <https://youtu.be/oaN78pB8vxw>`__
- The mupif/jupyter-demos repository on GitHub contains
  - `MuPIF Tutorial for beginners <https://github.com/mupif/jupyter-demos/blob/main/Introduction/index.ipynb>`__
  - `MuPIF Model API development tutorial <https://github.com/mupif/jupyter-demos/blob/main/API-development/index.ipynb>`__

Getting started with MuPIF 
======================



Simple workflow example
--------------------------
The executable representation of simulation workflow in MuPIF is a Python script in Python language implemented using basic bulding blocks (called components) defined by MuPIF. 
These components represent fundamental entities in the
model space (such as individual models (simulation tools), instances of data types, solution
steps, etc). The top level abstract classes are defind in MuPIF to represent these components, defining a common interface allowing to
manipulate individual representations using a single common interface.
The top level classes and their interfaces are described in :numref:`Platform-APIs`.

In this section, we present a simple, minimum working example,
illustrating the basic concept. The example presented in this section is
assumed to be executed locally. How to extend this and other examples into
distributed version is discussed in :numref:`sect-distributed-model`.

The following example illustrates the so-called
weak-coupling, where for each solution step, the first model
(m1) evaluates the value of concentration that is passed to
the second model (m2) which, based on provided
concentration values (DataID.PID_Concentration), evaluates the
average cumulative concentration
(DataID.PID_CumulativeConcentration). This is repeated for each
solution step. The example also illustrates, how solution steps can be
generated in order to satisfy time step stability requirements of
individual applications.


.. _list-simple-ex:
.. code-block:: python

   # Simple example illustrating simulation scenario

    import mupif as mp
    import model1
    import model2

    time = 0*mp.U.s
    timestepnumber = 0
    targetTime = 1.0*mp.U.s

    m1 = model1.Model1()  # create an instance of model #1
    m2 = model2.Model2()  # create an instance of model #2

    m1.initialize()
    m2.initialize()

    # loop over time steps
    while abs(time.inUnitsOf(mp.U.s).getValue() - targetTime.inUnitsOf(mp.U.s).getValue()) > 1.e-6:
        #determine critical time step
        dt2 = m2.getCriticalTimeStep()
        dt = min(m1.getCriticalTimeStep(), dt2)
        # update time
        time = time+dt
        if (time > targetTime):
            # make sure we reach targetTime at the end
            time = targetTime
        timestepnumber = timestepnumber + 1

        # create a time step
        istep = mp.TimeStep.TimeStep(time, dt, timestepnumber)
   
        try:
            #solve problem 1
            m1.solveStep(istep)
            #request temperature field from m1
            c = m1.get(mp.DataID.PID_Concentration, istep)
            # register temperature field in m2
            m2.set(c)
            # solve second sub-problem
            m2.solveStep(istep)
            prop = m2.get(mp.DataID.PID_CumulativeConcentration, istep)
            print ("Time: %5.2f concentraion %5.2f, running average %5.2f" % (istep.getTime(), c.getValue(), prop.getValue()))

        except APIError.APIError as e:
            logger.error("Following API error occurred: %s" % e )
            break

    # terminate the models
    m1.terminate();
    m2.terminate();


The full listing of this example can be found in
`examples/Example01 <https://github.com/mupif/mupif/tree/master/examples>`__.
The output is illustrated in :numref:`fig-ex1-out`.


.. _fig-ex1-out:
.. figure:: img/ex1-out.png

   Output from Example01.py

The platform installation comes with many examples, located in
*examples* subdirectory of platform installation and also accessible
`online <https://github.com/mupif/mupif/tree/master/examples>`__
in the platform repository. They illustrate various aspects, including
field mapping, vtk output, etc.



.. _Platform-APIs:

Platform APIs
================
As mentioned above, MuPIF key idea is based on composing simulation workflows from a set of components with standartized interfaces.  
In this chapter are presented the interfaces (APIs) for all relevenat entities. The interfaces, represented as a set of methods, are defined by abstract, top-level parent 
classes representing core component types (such as models or data types). The interfaces are inheritted by derived classes. 
This ensures, that all derived classes and their instances can be managed using the same interface.

One of the key and distinct features of the MuPIF
platform is that such an abstraction (defined by top level classes) is
not only developed for models, but also for the
simulation data. The focus is on services provided by objects
and not on underlying data. The object representation of data
encapsulates the data themselves, related metadata, and related
algorithms. Individual models then do not have to interpret the complex
data themselves; they receive data and algorithms in one consistent
package. This also allows the platform to be independent of particular
data format, without requiring any changes on the model side to work
with new format.

In the rest of this section, the fundamental, core classes and their
interfaces are presented with links to their documentation, generated directly from the source code using PyDoc package. 

.. _fig-abstract-uml:
.. figure:: img/MuPIF-basic-ontology.png

   MuPIF core classes and their relations

Common API
----------------------------------

The object-oriented approach allows to define hierarchy of classes. This
is also used in designing MuPIF class structure, where all component
classes form a hierarchy, where on top of this hierarchy is
:obj:`~mupif.mupifobject.MupifObject` class. This class introduces a common interface that is
then inherited by all derived classes, thus by all MuPIF components
involving models (Model class), workflows, and high-level data
components, such as properties or spatial fields.

The *MupifObject* class essentially defines methods allowing to get/set
metadata to the component. The metadata are identified by unique ID and
can be of any type. Internally, they are stored in internal dictionary
declared by *MupifObject.*


Metadata and metadata schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The metadata and metadata schemas in MuPIF are stored in a form of JSON
representations as a nested (hierarchical) dictionary. JSON stands for
“JavaScript Object Notation”, a simple data interchange format. In its
heart, JSON is built on the following data structures: object, array,
number, string, boolean and null. With these simple data types, all
kinds of structured data can be represented. The metadata structure in MuPIF is defined by the JSON schema, being a
template defining what fields are expected, and how the values are
represented. The advantage is that actual metadata and their structure can be validated against the schema. The JSON
schema itself is written in JSON (or as Pydantic data models, exporting the schema to JSON schema syntax). The JSON schema standard can be found
in [`11 <#2zd1531og9ob>`__].

As already mentioned, a schema in a Python in represented as a python dictionary,
with following keys: *type*, *properties*, and *required*.

-  The *type* defines the type of data. Can be any of the supported JSON
   types (object, array, number, string, boolean or null)

-  The *properties* is a dictionary containing the actual metadata in
   the from of key-value pairs, where values in the schema are
   dictionaries, containing ‘type’ key defining type of property.

-  The required key is an array containing required property keys.

As an example, let us consider an example of a subset of model metadata:

.. code-block:: python

   #Example of model schema (from Model.py)
   ModelSchema = {
     'type': 'object',
     'properties': {
         'Name': {'type': 'string'},
         'ID': {'type': ['string', 'integer']},
         'Description': {'type': 'string'},
         'Material': {'type': 'string'},
         'Physics': { 
           'type': 'object',
           'properties': {
             'Type': {'type': 'string', 'enum': ['Electronic', 'Atomistic', 'Molecular', 'Continuum', 'Other']},
             'Entity': {'type': 'string', 'enum': ['Atom', 'Electron', 'Grains', 'Finite volume', 'Other']}
             },
             'required': ['Type', 'Entity']
         },
     },
     'required': ['Name', 'ID', 'Description', 'Physics']
   }

The following listing shows valid metadata (according to schema defined
above):

.. code-block:: python

   # Example of valid metadata 
   metaData = {
     'Name': 'Stationary thermal problem',
     'ID': 'Thermo-1',
     'Description': 'Stationary heat conduction using finite elements on rectangular domain',
     'Geometry': '2D rectangle',
     'Physics': {
       'Type': 'Continuum',
       'Entity': 'Finite volume',
       'Equation': ['Heat balance'],
       'Equation_quantities': ['Heat flow'],
       'Relation_description': ['Fick\'s first law'],
       'Relation_formulation': ['Flow induced by thermal gradient on isotropic material'],
       'Representation': 'Finite volumes'
     },
   }


As illustrated, metadata can contain nested data structures. It is
possible to access the individual metadata entries by using convenience
methods provided by any *MupifObject* instance. Also, it is possible
to insert a new metadata entry to the structure. These methods allow to
use ‘dot’ notation to access nested entries, as illustrated in the
example below:


.. code-block:: python

   myobj.getMetadata ('Name') # returns 'Stationary thermal problem'
   myobj.getMetadata ('Physics.Type') #returns 'Continuum'
   myobj.setMetadata ('Physics.Representation', 'Finite elements') # change existing entry
   myobj.setMetadata ('Physics.NewNote', 'My note') # add a new entry to metadata


The metadata schemata are defined in corresponding modules. In MuPIF,
the metadata schemata are defined for *Model*, *Workflow*, and some other data
classes. Generated documentation of the JSON schemata for selected components is available in :numref:`sect-schemas-doc`.



Model class
----------------

The abstract :obj:`~mupif.model.Model` class represents a model. Model is a component in general performs some operation on data, it can have input and output parameters. In terms of MODA [9] nomenclature, introduced by EMMC
[10], the instances of *Model* class correspond to MODA models and post-processing tools, but model in MuPIF can also represent an interface to external database, for example. 

The model interface is defined in terms of abstract services for
data exchange and steering. Derived classes represent individual
simulation models. The data exchange services consist of methods for getting and
registering external properties, fields, and functions, which are
represented using corresponding, newly introduced classes. Steering
services allow invoking (execute) solution for a specific solution step,
update solution state, terminate the application, etc.


Workflow class
-------------------

The :obj:`~mupif.workflow.Workflow` class represents a simulation workflow. Workflow can
combine several models into a complex simulation task. The workflow definition combines (1) execution model determining, 
how individual models are executed and (ii) data model determining the data exchange between models and workflow I/O parameters.  
A key feature of *Workflow* class is that it is derived from *Model*
class, so it shares the same API as *Model* Interface.
This essentially allows to treat any *Workflow* as *Model* and allows to
build a hierarchy of nested workflows. 

Property class
-------------------

:obj:`~mupif.property.Property` is a data type representing a quantity, which has no spatial
variation. Property is identified by *PropertyID*, which is an
enumeration determining its physical meaning. It can represent any
quantity of a scalar, vector, or tensorial type. Property keeps its
value, type, associated time and an optional *objectID*, identifying
related component/subdomain.


Property with constant value in time is represented by
:obj:`~mupif.property.ConstantProperty` class derived from :obj:`~mupif.property.Property`.


Field class
----------------

:obj:`~mupif.field.Field` is a data type representing a field, which is a scalar, vector, or tensorial
quantity defined on a spatial domain (represented by the :obj:`mupif.mesh.Mesh` class, for example).
The field provides interpolation services in space, but is assumed to be
fixed in time (the model interface allows to request field at
specific time). 
The field can be evaluated in any spatial point belonging to underlying
domain. Derived classes will implement fields defined on common
discretizations, like fields defined on structured or unstructured FE
meshes, finite difference grids, etc. 


Function class
-------------------

:obj:`~mupif.function.Function` class represents a component transforming given inputs to outputs. It is similar to model, but it is supposed to represent rather simple relation and not complex model.
Typically, function is an object defined by
mathematical expression and can be a function of spatial position, time,
and other variables. Derived classes should implement evaluate service
by providing a corresponding expression. The function arguments are
packed into a dictionary, consisting of pairs (called items) of keys and
their corresponding values.


TimeStep class
-------------------

:obj:`~mupif.timestep.TimeStep` class represents solution time step. The time step manages its number,
target time, and time increment.


.. _fig-timestep:
.. figure:: img/timestep.png

   Concept of time step in MuPIF

Mesh class
---------------

:obj:`~mupif.mesh.Mesh` is an abstract representation of a computational domain and
its spatial discretization. The mesh geometry is described using
computational cells (representing finite elements, finite difference
stencils, etc.) and vertices (defining cell geometry). Derived classes
represent structured, unstructured FE grids, FV grids, etc. Mesh is
assumed to provide a suitable instance of cell and vertex localizers. In
general, the mesh services provide different ways how to access the
underlying interpolation cells and vertices, based on their numbers, or
spatial location.


Cell class
---------------

:obj:`~mupif.cell.Cell` represents a computational cell (finite element, for example). The solution
domain is composed of cells, whose geometry is defined using vertices.
Cells provide interpolation over their associated volume, based on given
vertex values. Derived classes will be implemented to support common
interpolation cells (finite elements, FD stencils, etc.)


Vertex class
------------------

:obj:`~mupif.vertex.Vertex` represents a vertex. In general, a set of vertices defines the geometry
of interpolation cells. A vertex is characterized by its position,
number and label. Vertex number is locally assigned number (by *Mesh*
class), while a label is a unique number defined by application.


BoundingBox
-----------------

:obj:`~mupif.boundingbox.BoundingBox` represents an axis aligned bounding box - a rectangle in 2d and a prism
in 3d. Its geometry is described using two points - lover left and upper
right. The bounding box class provides fast and efficient methods for
testing whether point is inside and whether an intersection with another
bounding box exists.

HeavyStruct
--------------

:obj:`~mupif.heavystruct.HeavyStruct` is self-describing container for complex, hierarchical data with user-defined structure and with remote/local access. 
The data is described using JSON (which can be validated using JSON schema), stored next to the data. 
The backing storage format is HDF5 (which is hidden from the user via API). Provisions are present for ontological metadata so that each item can have ontological meaning.


APIError
--------------

:obj:`~mupif.apierror.APIError` serves as a base class representing  exceptions thrown by the
individual components. Raising an exception is a way to signal that a routine could
not execute normally - for example, when an input argument is invalid
(e.g. value is outside of the domain of a function) or when a resource
is unavailable (like a missing file, a hard disk error, or out-of-memory
errors). A hierarchy of specialized exceptions can be developed, derived
from the *APIError* class.

Exceptions provide a way to react to exceptional circumstances (like
runtime errors) in programs by transferring control to special functions
called handlers. To catch exceptions, a portion of code is placed under
exception inspection. This is done by enclosing that portion of code in
a try-block. When an exceptional circumstance arises within that block,
an exception is thrown that transfers the control to the exception
handler. If no exception is thrown, the code continues normally and all
handlers are ignored.

An exception is thrown by using the throw keyword from inside the
try-block. Exception handlers are declared with the keyword "except",
which must be placed immediately after the try block.




Developing Application Program Interface (API)
=================================================

In order to establish an interface between the platform and external model, a new class derived from base *Model* class has to be created, essentially implementing MuPIF *Model* interface.  
The *Model* class defines a
generic interface in terms of general purpose, problem independent,
methods that are designed to steer and communicate the model.
This table presents an overview of application interface, the full
details with complete specification can be found in :obj:`~mupif.model.Model`.

======================================================= ==========================================================================
Method                                                  Description
\__init__(self, metaData)                               Constructor. Initializes the application.
initialize(self, workdir, metaData, validateMetaData)   Initializes model and sets workdir and metadata.
get(self, objectTypeID, time=None, objectID="")         Returns an output of the model, specified by objectTypeID and objectID.
set(self, obj, objectID="")                             Sets an input of the model, specified by objectID and type of obj.
solveStep(self, tstep)                                  Solves the problem for given time step.
finishStep(self, tstep)                                 Called after a global convergence within a time step.
getCriticalTimeStep()                                   Returns the actual critical time step increment.
getAssemblyTime(tStep)                                  Returns assembly time within a timestep
getApplicationSignature()                               Returns the application identification
terminate()                                             Terminates the application.
======================================================= ==========================================================================

From the perspective of individual simulation tool, the interface
implementation can be achieved
by means of either direct (native) or indirect implementation.

-  **Native implementation** of a *Model* interface requires model written in
   Python, or a model with Python interface. In this case the *Model*
   methods will be implemented directly using direct calls to suitable
   application’s functions and procedures, including necessary internal
   data conversions. In general, each application (in the form of a
   dynamically linked library) can be loaded and called, but care must
   be taken to convert Python data types into target application data
   types. More convenient is to use a wrapping tool (such as Swig [11],
   Boost [12] or PyBind11 [13]) that can generate a Python interface to the application,
   generally taking care of data conversions for the basic types. The
   result of wrapping is a set of Python functions or classes,
   representing their application counterparts. The user calls an
   automatically generated Python function which performs data
   conversion and calls the corresponding native equivalent.

-  **Indirect implementation** of a *Model* interface is based on wrapper class implementing
   Model interface that implements the interface indirectly, using, for
   example, simulation tool scripting or I/O capabilities. In this case
   the application is typically standalone application, executed by the
   wrapper in each solution step. For the typical solution step, the
   wrapper class has to cache all input data internally (by overloading
   corresponding set methods), execute the application from previously
   stored state, passing input data, and parsing its output(s) to
   collect return data (requested using get methods).

The example illustrating the indirect implementation is discussed
further. The basics are the same, one has to define a new class derived from *Model* class, representing the interface to new (external) model. 
The implementation of this class has to provide implementation of all *Model* services, that require to establish communication channel to external model. 
Here we assume that no direct communication is available so we need to communicate with an external model indirectly, typically using files. 
The important fact is that this communication mechanism is only part of specific model class instance and is therefore hidden behing generic *Model* interface. 
Typical procedure consists of three steps. In the first step,
when input parameters of the meodel are being set (using *set* method), the class representing a new model 
has to remember all input parameters. In the second step, when the
application is to be executed (using *solveStep* method), the tepmplate input file (which is assumed to exist) is used to produce the actual input file with substituted values of input parameters. 
After the input file(s) are generated, the
application itself is executed, typically producing output file(s) with results. In the last step, when the actual model output parameters are requested (using the *get* method), 
the cooresponding values are obtained by parsing output files generated.

To ilustrate this concept, we present an example of implementing MuPIF interface to a model 
computing the average value from property (concentration) time history. Suppose now, that we want to use the existing external application, that can compute an average value from given input values
read from a file. The application interface accumulates the input values
of concentrations in a list, this is done is *set*
method. During the solution (*solveStep* method), the accumulated
values of concentrations over the time are written into a file, the
external application is executed, reading the created file as input and
producing an output file containing the computed average. The output
file is parsed when the average value is requested (*get*
method).

.. _fig-indirect-api:
.. figure:: img/MuPIF-Indirect-api.*

   Typical workflow in indirect approach for API implementation


Developing user workflows
============================

Multiscale/multiphysics simulations are natively supported in MuPIF,
allowing easy data passing from one model to another one, synchronizing
and steering all models. Simulation workflow of multiscale/multiphysics
simulations, called also a simulation scenario, need to define (1) execution model (steering of models) and (2) data model (defines how data are passed/exchanged). Natively, the workflow in MuPIF is
represented as Python script combining MuPIF components into workflow. 
 

Workflow templates
--------------------


Sequential
~~~~~~~~~~~~~

.. figure:: img/workflow-sequential.png

   Sequential workflow template


.. code-block:: python

    time = 0*mp.U.s
    timeStepNumber = 0
    targetTime = 10*mp.U.s

    while (abs(time-targetTime).getValue() > 1.e-6):
        dt=min(
            m1.getCriticalTimeStep(),
            m2.getCriticalStep(),
            m3.getCriticalStep()
        )
        time = time+dt
        if (time > targetTime):
            time = targetTime

        timeStepNumber = timeStepNumber + 1
        istep=TimeStep.TimeStep(time, td, targetTime, n=timeStepNumber)
        try:
            m1.solveStep(istep)
            p = m1.get(PID, m2.getAssemblyTime(istep))
            m2.set(p)
            m2.solveStep(istep)
            # ...
            m3.solveStep(istep)
        except APIError.APIError as e:
            print ("API Error occurred:", e)
            break

    m1.terminate()
    m2.terminate()
    m3.terminate()


Loosely coupled
~~~~~~~~~~~~~~~~


.. figure:: img/workflow-loosely-coupled.png

   Loosely coupled workflow template


.. code-block:: python

    time = 0*mp.U.s
    timeStepNumber = 0
    targetTime = 10*mp.U.s

    while (abs(time-targetTime).getValue() > 1.e-6):
        dt = min(
            m1.getCriticalTimeStep(),
            m2.getCriticalStep(),
            m3.getCriticalStep()
        )
        time = time+dt
        if (time > targetTime):
            time = targetTime
        timeStepNumber = timeStepNumber + 1
        istep = TimeStep.TimeStep(time, td, targetTime, n=timestep)

        try:

            convergedFlag = False
            while not convergedFlag:
                m1.solveStep(istep)
                p1 = m1.get(data_id, m2.getAssemblyTime(istep))
                m2.set(p1)
                m2.solveStep(istep)
                p2 = m2.get(data_id2, m1.getAssemblyTime(istep))
                m1.set(p2)

                #check for convergence
                convergedFlag = checkConvergence()

            m3.solveStep()

        except APIError.APIError as e:
            print ("API Error occurred:", e)
            break

    m1.terminate()
    m2.terminate()
    m3.terminate()


Workflow example
---------------------
To ilustrate the concept, a simple example of steady state, sequential, multiphysic, thermo-mechanical workflow in two dimensional domain is presented. 
The full implementation is available under *examples/Example06\**
directory of MuPIF installation.

The workflow combines thermal model, solving energy balance and yielding termal field and mechanical model, solving momentum balance equations, 
yielding primarily displacement field and also strain and stress fields, obtained by postprocessing the displacement field. 

In presented example, we consider a domain representing simple cantilever, clamped on the left hand side and subjected to
thermal loading, see :numref:`fig-cantilever-thermal`. Heat convection is
prescribed on the top edge with ambient temperature 10°C. Left and
bottom edges have prescribed temperature 0°C, the right edge has no
boundary condition. Initial temperature is set to 0°C, heat conductivity
is 1 W/m/K, heat capacity 1.0 J/kg/K, material density 1.0
kg/m³. The material has assigned Young's modulus as 30 GPa,
Poisson's ratio 0.25 and coefficient of linear thermal expansion
12e-6°C⁻¹.

.. _fig-cantilever-thermal:
.. figure:: img/cantilever-thermal.png

   Elastic cantilever subjected to thermal boundary conditions.

The schema of the workflow is depicted in
:numref:`fig-thermo-mech-flow`. 

A workflow can be regardes as a computational receipe and be represented as a plain Python script. But there are many advantages of representing a workflow as a class. 
Generally speaking, any workflow can be considered as a (more complex) model, that has specific inputs and outputs. 
The object oriented design of MuPIF allows to naturally represent this concept, introducing *Workflow* class as a base class for all workflow implementations, derived from *Model* class. 
This essentially allows to build a hierarchy of
workflows, where the top level workflow may utilise existing models and workflows. Another important advantage of having workflow represented as a class is
that the individual workflows can be allocated and executed by a
jobManager on remote resources in a same way as individual applications.

By following the concept of representing a workflow as a class, the workflow has to define its metadata and implement similar methods as model, including *set* and *get* methods to map inpouts and outputs, and *solveStep* method. The *Workflow* class defines additional method *solve*
to generate the time loop over the individual time steps, subsequently solved by
*solveStep* method.

Back to our example. First, the temperature distribution has to be solved in the whole domain
from the given initial and boundary conditions. Here we assume for simplicity, that the thermal problem is defined in model specific template, that is passed to thermal model (using *set method).
The template can be further instanciated using selected input parameters (not done here).
Next, the thermal model is updated/solved (*solveStep* method) and resulting steady state temperature field is requested (*get* method) and 
passed afterwards to the mechanical model (*set* method), which is updated as well (*solveStep*) and finally, the
corresponding displacement field is available. 

.. _fig-thermo-mech-flow:
.. figure:: img/thermo-mech-flow.png

   Thermo-mechanical simulation flow


One of the adantages, originating from representing spatil fields as data Type), is that the discretizations for thermal and mechanical problems can be 
different, as the thermal field takes care of field
interpolation. The mesh for thermal problem consist of 50 linear
elements with linear approximation and 55 nodes. The mesh for mechanical
analysis consist of 168 nodes and 160 elements with linear
approximation. Results for final step are shown in :numref:`fig-thermo-mech-results`.

.. _fig-thermo-mech-results:
.. figure:: img/thermo-mech-results.png

   Results of thermo-mechanical simulation

A code below documents an execution of  thermo-mechanical simulation in *Example06*.
The implementation of thermal and mechanical solvers are provided in *demoapp* module.

.. code-block:: python


    class Example06(mp.Workflow):

        def __init__(self, metadata=None):
            MD = {
                'Name': 'Thermo-mechanical stationary problem',
                'ID': 'Thermo-mechanical-1',
                'Description': 'stationary thermo-mechanical problem using finite elements on rectangular domain',
                # 'Dependencies' are generated automatically
                'Version_date': '1.0.0, Feb 2019',
                'Inputs': [],
                'Outputs': [
                    {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Temperature', 'Name': 'Temperature field',
                     'Description': 'Temperature field on 2D domain', 'Units': 'degC'},
                    {'Type': 'mupif.Field', 'Type_ID': 'mupif.DataID.FID_Displacement', 'Name': 'Displacement field',
                     'Description': 'Displacement field on 2D domain', 'Units': 'm'}
                ],
                'Models': [
                    {
                        'Name': 'thermal',
                        'Module': 'mupif.demo',
                        'Class': 'ThermalModel'
                    },
                    {
                        'Name': 'mechanical',
                        'Module': 'mupif.demo',
                        'Class': 'MechanicalModel'
                    }
                ]
            }
            super().__init__(metadata=MD)
            self.updateMetadata(metadata)

        def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
            super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

            thermalInputFile = mp.PyroFile(filename='inputT.in', mode="rb", dataID=mp.DataID.ID_InputFile)
            self.getModel('thermal').set(thermalInputFile)

            mechanicalInputFile = mp.PyroFile(filename='inputM.in', mode="rb", dataID=mp.DataID.ID_InputFile)
            self.getModel('mechanical').set(mechanicalInputFile)

        def solveStep(self, istep, stageID=0, runInBackground=False):
            self.getModel('thermal').solveStep(istep, stageID, runInBackground)
            self.getModel('mechanical').set(self.getModel('thermal').get(DataID.FID_Temperature, istep.getTime()))
            self.getModel('mechanical').solveStep(istep, stageID, runInBackground)

        def get(self, objectTypeID, time=None, objectID=""):
            if objectTypeID == DataID.FID_Temperature:
                return self.getModel('thermal').get(objectTypeID, time, objectID)
            elif objectTypeID == DataID.FID_Displacement:
                return self.getModel('mechanical').get(objectTypeID, time, objectID)
            else:
                raise apierror.APIError('Unknown field ID')

        def getCriticoalTimeStep(self):
            return 1*mp.U.s

        def getApplicationSignature(self):
            return "Example06 workflow 1.0"

        def getAPIVersion(self):
            return "1.0"


    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }

    demo = Example06()
    demo.initialize(metadata=md)
    demo.set(mp.ConstantProperty(value=1.*mp.U.s, propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s), objectID='targetTime')

    tstep = timestep.TimeStep(time=1*mp.U.s, dt=1*mp.U.s, targetTime=10*mp.U.s)

    demo.solveStep(tstep)

    tf = demo.get(DataID.FID_Temperature, tstep.getTime())
    t_val = tf.evaluate((4.1, 0.9, 0.0))

    mf = demo.get(DataID.FID_Displacement, tstep.getTime())
    m_val = mf.evaluate((4.1, 0.9, 0.0))
    print(t_val.getValue()[0], m_val.getValue()[1])

    demo.printMetadata()
    demo.terminate()

As already mentioned, the thermo-mechanical simulation workflow can run in
various configurations, starting from simplest, local setup to distributed one, where each of the models runs on remote resources.  Table 3 shows available examples of thermo-mechanical
configurations. 

.. |image-therm| image:: img/app-therm.png
.. |image-mech| image:: img/app-mech.png

.. csv-table:: Examples of thermo-mechanical simulation on local and various distributed configurations.

   ,Steering script,Nameserver,Thermal application |image-therm|,Mechanical application |image-mech|
   Example06 (local),Local,-,Local,Local
   "Example07 (JobMan, VPN, ssh)",Local,Remote,"Remote, JobMan","Remote, JobMan"
   "Example08 (JobMan, VPN, ssh)",Local,Remote,"Remote, JobMan",Local

.. _sect-distributed-model:

Distributed Model
====================

Common feature of parallel and distributed environments is a distributed
data structure and concurrent processing on distributed processing
nodes. This brings in an additional level of complexity that needs to be
addressed. To facilitate execution and development of the simulation
workflows, the platform provides the transparent communication mechanism
that will take care of the network communication between the objects. An
important feature is the transparency, which hides the details of remote
communication to the user and allows to work with local and remote
objects in the same way.

The communication layer is built on `Pyro
library <https://pythonhosted.org/Pyro5/>`__ [4], which provides a
transparent distributed object system fully integrated into Python. It
takes care of the network communication between the objects when they
are distributed over different machines on the network. One just calls a
method on a remote object as if it were a local object – the use of
remote objects is (almost) transparent. This is achieved by the
introduction of so-called proxies. A proxy is a special kind of object
that acts as if it were the actual object. Proxies forward the calls to
the remote objects, and pass the results back to the calling code. In
this way, there is no difference between simulation script for local or
distributed case, except for the initialization, where, instead of
creating local object, one has to connect to the remote object.

.. _fig-local-remote-comm:
.. figure:: img/local-remote-comm.*

   Comparison of local vs. remote object communication scenarios


To make an object remotely accessible, it has to be registered with the
daemon, a special object containing server side logic which dispatches
incoming remote method calls to the appropriate objects. To enable
runtime discovery of the registered objects, the name server is
provided, offering a phone book for Pyro objects, allowing to search for
objects based on logical name. The name server provides a mapping
between logical name and exact location of the object in the network, so
called uniform resource identifier (URI). The process of object
registration and of communication with remote objects (compared to local
objects) is illustrated in :numref:`fig-local-remote-comm`.

Distributed aspects of the API
-----------------------------------

One of the important aspect in distributed model is how the data are
exchanged between applications running at different locations. The Pyro5
communication layer allows to exchange data in terms of get and set API
methods in two ways. The communication layer automatically takes care of
any object that is passed around through remote method calls. The
receiving side of a call can receive either a local copy of the remote
data or the representation of the remote data (Proxy).

-  The communication in terms of exchanging local object copies can be
   less efficient than communication with remote objects directly, and
   should be used for objects with low memory footprint. One potential
   advantage is that the receiving side receives the copy of the data,
   so any modification of the local copy will not affect the source,
   remote data. Also multiple method invocation on local objects is much
   more efficient, compared to costly communication with a remote
   object.

-  On the other hand, the data exchange using proxies (references to
   remote data) does not involves the overhead of creating the object
   copies, which could be prohibitively large for complex data
   structures. Also, when references to the remote objects are passed
   around, the communication channel must be established between
   receiving side and remote computer owning the actual object, while
   passing local objects requires only communication between caller and
   receiver.

Both approaches have their pros and cons and their relative efficiency
depends on actual problem, the size of underlying data structures,
frequency of operations on remote data, etc.

Pyro5 will automatically take care of any Pyro5 objects that you pass
around through remote method calls. If the autoproxying is set to on
(AUTOPROXY = True by default), Pyro5 will replace objects by a proxy
automatically, so the receiving side can call methods on it and be sure
to talk to the remote object instead of to a local copy. There is no
need to create a proxy object manually, a user just has to register the
new object with the appropriate daemon. This is a very flexible
mechanism, however, it does not allow explicit control on the type of
passed objects (local versus remote).

Typically, one wants to have explicit control whether objects are passed
as proxies or local copies. The get methods (such as *getProperty*,
*getField*) should not register the returned object at the Pyro5 daemon.
When used, the remote receiving side obtains the local copy of the
object. To obtain the remote proxy, one should use *getFieldURI* API
method, which calls getField method, registers the object at the server
daemon and returns its URI. The receiving side then can obtain a proxy
object from URI. This is illustrated in the following code snippet:

.. code-block:: python

   field_uri = Solver.getFieldURI(DataID.FID_Temperature, 0.0)
   field_proxy = Pyro5.Proxy(uri)

Requirements for distributed computing
-------------------------------------------

To enable the discovery of remote objects a nameserver service is
required, allowing to keep track of individual objects in network. It is
also allows to use readable uniform resource identifiers (URI) instead
of the need to always know the exact object id and its location.

The platform is designed to work on virtually any distributed platform,
including grid and cloud infrastructure. For the purpose of performing
simulations within a project, it is assumed that individual simulations
and therefore the individual simulation packages will be distributed
over the network, running on dedicated servers provided by individual
partners, forming grid-like infrastructure.

The MuPIF also supports integration of HPC recources, providing a support for simple integration of models running on HPC hardware.


Internal platform solution - ModelServer resource allocation
----------------------------------------------------------------

This solution has been developed from a scratch targeting fulfilment of
minimal requirements only while providing simple setup. The resource
allocation is controlled by *ModelServer*. Each computational server
within a platform should run an instance of ModelServer, which provides
services for allocation of application instances based on user request
and monitoring services.

The *ModelServer* is implemented as python object like any other platform
components and is part of platform source code. It is necessary to
create an instance of *ModelServer* on each application server and
register it on the platform nameserver to make it accessible for clients
running simulation scenarios. This allows to access *ModelServer*
services using the same Pyro technology, which makes the resource
allocation to be part of the the simulation scenario. Typically, the
simulation scenario script first establishes connection to the platform
nameserver, which is used to query and create proxies of individual
*ModelServers*. The individual *ModelServers* are subsequently requested
to create the individual application instances (using *allocateJob*
service) and locally represented by corresponding proxy objects.
Finally, the communication with remote application instances can be
established using proxies created in the previous step, see :numref:`fig-jobmanager-control-flow`
illustrating typical work flow in the distributed case.

The model server has only limited capability to control allocated
resources. In the present implementation, the server administrator can
impose the limit on number of allocated applications. The configuration
of the jobmanager requires only simple editing of configuration file.
The individual applications are spawned under new process to enable true
concurrency of running processes and avoid limitations of Python related
to concurrent thread processing.

.. _fig-jobmanager-control-flow:
.. figure:: img/jobmanager-control-flow.*

   Typical control flow with resource allocation using ModelServer.

The status of individual model servers can be monitored with the
jobManStatus.py script, located in tools subdirectory of the platform
distribution. This script displays the status of individual jobs
currently running, including their run time and user information. The
information displayed is continuously refreshed, see :numref:`fig-jobman-monitor`.

.. _fig-jobman-monitor:
.. figure:: img/jobman-monitor.png

   Screenshot of model server monitoring tool

The internal jobManager does not provide any user authentication service
at the moment. The user access is assumed to be controlled externally,
using ssh authorization. For example, to establish the authorized
connection to a remote server and platform services (jobManager) using a
ssh tunnel, a valid user credentials for the server are required. The
secured, authenticated connection is realized using setting up ssh
tunnel establishing a secure and trusted connection to a server. The ssh
connections can be authorized by traditional user/passwords or by
accepting public ssh keys generated by individual clients and send to
server administrators. More details are given in a Section on SSH
tunneling.

The status of individual computational servers can be monitored online
using the provided monitoring tool. A simple ping test can be executed,
verifying the connection to the particular server and/or allocated
application instance.

Setting up a Model Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The skeleton for application server is distributed with the platform and
is located in *examples/Example04-JobMan-distrib*.

The ``sever.py`` script runs the model server itself; it will become available for incoming connection (at an arbitrary port number, which is reachable from all clients in the VPN; see :numref:`sect-platform-installation` for details) and registers itself in the name server. Model will be then instantiated and executed upon request. (the :obj:`~mupif.ModelServer.runServer` is responsible for executing these steps).

Model server configuration options are :obj:`documented in the reference manual <mupif.ModelServer>`; of particular importance are the following parameters:

- ``ns``: name server is found via :obj:`mupif.pyroutil.connectNameserver` (the logic of using ``MUPIF_NS`` environemnt variable or configuration file is described in :numref:`sect-nameserver`);
- ``appClass``: model class;
- ``appName``: name under which the model will be registered in the name server;
- :obj:`~mupif.ModelServerBase.maxJobs` limiting the number of concurrent instances running;

:numref:`fig-thermo-mech-vpn` shows the distributed model running atop the VPN.

.. _fig-thermo-mech-vpn:
.. figure:: img/thermo-mech-vpn.*

   *Example16* thermo-mechanical analysis displaying ports in a distributed setup using VPN.


To start an application server run (*Example04-JobMan-distrib*)::

   $ python3 server.py

The command logs on screen and also in the ``server.log`` logfile the individual requests (as configured within ``setup.py``).

The status of the all model servers can be shown on-line from any computer by running (provided ``MUPIF_NS`` is set correctly)::

   $ python3 -m mupif.cli servers


.. code-block:: json

   [
       {
           "ns": {"name": "CVUT.demo01", "uri": "PYRO:obj_aca860f9d7834f2e8f8c81097f4981e2@172.24.1.1:38605", "metadata": {"type:jobmanager"}},
           "numJobs": {"max": 4, "curr": 0, "total": 4303},
           "jobs": [],
           "status": true,
           "signature": "Mupif.JobManager.ModelServer"
       }
   ]




.. monitored on-line from any computer using ``tools/jobManStatus.py`` monitor. To start monitoring, run e.g. the following command::

      $ python3 jobManStatus.py -j Mupif.ModelServer@Example -n 127.0.0.1*

   The -j option specifies the jobmanager name (as registered in pyro
   nameserver), -h determines the hostname where jobmanager runs, -p
   determines the port where jobmanager is listening, -n is hostname of the
   nameserver, see :numref:`fig-screen-jobman-test`.

   .. _fig-screen-jobman-test:
   .. figure:: img/screen-jobman-test.png

      Testing model server in a simple setup

   There is also a simple test script (tools/jobManTest.py), that can be
   used to verify that the installation procedure was successful. It
   contact the application server and asks for new application instance.

.. _HPC:

HPC integration
--------------------------------------
The massively parallel simulations on HPC are typically run in scheduled execution mode, which ensures optimal allocation and use of resources. 
In this model, the user creates a job description file, describing what are the inputs, outputs, what to execute and specify resource allocation requirements (number of nodes, memory, required runtime).
The job is subsequently submitted and later executed by the HPC scheduling system when resources are available. 
In addition, there is typically no possibility of running permanent services on HPC side. 
This mode of operation has certain implications on how the HPC model interface is to be implemented.  

The efficient use of HPC resources requires that all needed pre and post processing should be done outside HPC, and only actual model execution be performed using HPC. 
Individual ModelServers responsible for interacting with simulation workflows must ensure, that resource allocation, preprocessing inputs and postprocessing outputs for 
or from actual model execution is done without using HPC resources, i.e., must be done before or after submitting the job and only the model execution phase should utilize HPC. 
This implies the need for running the model APIs on dedicated server (external resource to HPC), which interacts with HPC batch system to schedule the actual model execution.  

Additional considerations should be taken when the model is executed from workflow within time loop involving the data exchange with other models. 
The efficient utilization of HPC resources generally implies that in such a case, the model API should schedule the execution for individual time step 
updates of the model, and this may require the model API to support restart capability from saved state, to prevent model utilizing costly HPC resources when 
waiting for potentially other models involved in the time loop.  

There are different HPC integration levels possible with different requirements. 
Here we follow the less intrusive (from the HPC perspective) integration, illustrated on :numref:`fig-hpc-integration`. The requirements are following: 

- A dedicated platform user account needs to be set up on HPC side, allowing to perform file transfer and job submission. 
  On HPC, standardized job scheduling subsystem is required ​(SLURM Workload manager, 2021)​,​ (Wikipedia article on Portable Batch System, 2021)​. 

- External MuPIF node running ModelServer service for models to be executed on HPC (with MuPIF installation). 
  The node will also run individual model APIs, responsible for input collection, preparation of job scripts and their scheduling on HPCs, monitoring execution and result collection. 
  The node must have network connectivity to HPC infrastructure allowing to perform file transfer and job submission using HPC credentials.  
  
 
.. _fig-hpc-integration:
.. figure:: img/hpc-integration.png

   Schema of 3rd party HPC integration 

 

The MuPIF platform has been extended to provide dedicated HPC integration layer, that abstracts the various aspects of HPC integration: secure data transfer, 
job submission and monitoring. Both mainstream job submission systems (PBS, SLURM) are supported. 



.. _VPN:

Using Virtual Private Network (VPN)
--------------------------------------

Generalities
~~~~~~~~~~~~~~~~~~~

Virtual Private Networks (VPN) provide encryption and
authorization services. The VPNs work on a lower level of communication
(OSI Layer 2/3) by establishing “virtual” (existing on the top of other
networks) network, where all nodes have the illusion of direct
communication with other nodes through TCP or UDP, which have IP
addresses assigned in the virtual network space, see :numref:`fig-vpn-arch`. The VPN
itself communicates through existing underlying networks, but this
aspect is not visible to the nodes; it includes data encryption,
compression, routing, but also authentication of clients which may
connect to the VPN. `Wireguard <https://wireguard.org/>`__ is a major
implementation of VPN, and is supported on many platforms, including
Linux, Windows, Android and others.

Using VPN with MuPIF, the infrastructure must be set up beforhand, but clients
can communicate in a secure manner without any additional provisions -
it is thus safe to pass unencrypted data over the VPN, as authentication
has been done already.

Note that all traffic exchanged between VPN clients will go through the
VPN server instance; the connection of this computer should be fast
enough to accommodate all communication between clients combined.


.. _fig-vpn-arch:
.. figure:: img/vpn-arch.*

   VPN architecture

.. _sect-vpn-setup:

VPN Set-up
~~~~~~~~~~~~

Since wireguard is realtively low-level VPN architecture, it is very flexible in terms of topology. MuPIF uses `Star network topology <https://en.wikipedia.org/wiki/Star_network>`__.

Becoming a part of the VPN network comprises the following:

1. Obtaining Wireguard configuration from the central hub administrators (they coordinate IP address assignment to clients);

2. Ensuring that the VPN endpoint (the ``Peer``/``Endpoint`` entry in the config file) is reachable from your machine (it runs at a dedicated port, so ensure your local network is not blocking outbound traffic to that IP/port).

   .. note:: The node does not need to be reachable from outside, thus it is not necessary to open firewall for inbound traffic. The node establishes UDP connection to the hub, and it is kept open via periodic keep-alive packet from node to the hub (every 30s in usual configurations, via ``Peer/PersistentKeepalive`` option).

3. Deploying the configuration on the local node.

   * Windows: the configuration file can be imported straght into the Wireguard client.
   * Linux, two options:

     * the config file is copied into ``/etc/wireguard/somename.conf`` (the name is arbitrary) and the VPN is started with `sudo wg-quick somename` (or started persistently with `sudo systemctl enable --now wg-quick@somename`.
     * the config file is imported into NetworkManager via ``sudo nmcli connection import type wireguard file configfile.conf`` and subsequently the connection is saved persistently in NetworkManager and can be activated as other network connections. (You will need the wireguard module for NetworkManager installed for this to work)

Confirm that VPN connection works by pinging the central hub. The config file contains e.g. ``Address = 172.22.2.13/24``; replace the last number by ``1`` and test ping onto the machine: ``ping 172.22.2.1``. If the IP address is IPv6 (e.g. ``Address = fd4e:6fb7:b3af:0000::12/32``), also replace the last number by ``1``: ``ping fd4e:6fb7:b3af:0000::1``. If the ping responds, your VPN connection is working.

Whenever node connects to the Wireguard endpoint, the following happens:

#. The node is authenticated via its public key (stored in the hub);

#. New network interface is created on the node, with IP address as specified in the Wireguard config file.

#. Routing is established such that *only* VPN traffic is routed through the hub.

#. The node is sending periodic keep-alive packets to the hub (``Peer/PersistentKeepalive`` option) so that di-directional connection is always possible.


.. warning:: Do not install the same Wireguard configuration on multiple machines. Simultaneous connection to the hub would result in connection malfunction. If you need to connect several machines, request several Wireguard configurations.


Example of simulation scenario using VPN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The process of allocating a new instance of remote application is
illustrated on adapted version of the local thermo-mechanical scenario,
already presented in `7. Developing user workflows <#_8g4hbmxvvsu4>`__.
VPN mode can be enforced by issuing commands with *-m 2* at the end.
Refer to *examples/Example07-stacTM-JobMan-distrib*.

Online Monitoring tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To monitor the status of VPN network as well as status of the MuPIF
infrastructure, an online monitoring tool has been developed. It is
based on OpenVPN-monitor tool, which monitors the status of VPN server
and connected VPN clients. It has been extended to display stats about
status of MuPIF infrastructure. It shows the status of the nameserver,
the list of registered jobManagers, their connection information and
number of running tasks. The monitoring tool is accessible from any web
browser running on a computer connected to the VPN network.

.. figure:: img/screen-vpn.png

   Screenshot of VPN and platform monitoring tool


References
==============

#. D1.1 Application Interface Specification, MMP Project, 2014.

#. D1.2 Software Requirements Specification Document for Cloud
   Computing, MMP Project, 2015.

#. Python Software Foundation. Python Language Reference, version 3.5.
   Available at `http://www.python.org <http://www.python.org/>`__

#. Pyro - Python Remote Objects,
   ` <http://pythonhosted.org/Pyro5>`__\ http://pythonhosted.org/Pyro

#. B. Patzák, D. Rypl, and J. Kruis. MuPIF – a distributed multi-physics
   integration tool. Advances in Engineering Software, 60–61(0):89 – 97,
   2013
   (http://www.sciencedirect.com/science/article/pii/S0965997812001329).

#. B. Patzak, V. Smilauer, and G. Pacquaut, accepted presentation &
   paper “\ *Design of a Multiscale Modelling Platform*\ ” at the
   conference Green Challenges in Automotive, Railways, Aeronautics and
   Maritime Engineering, 25\ :sup:`th` - 27\ :sup:`th` of May 2015,
   Jyväskylä, Finland.

#. B. Patzak, V. Smilauer, and G. Pacquaut, presentation & paper
   “\ *Design of a Multiscale Modelling Platform*\ ” at the 15 :sup:`th`
   International Conference on Civil, Structural, and Environmental
   Engineering Computing, 1\ :sup:`st` - 4\ :sup:`th` of September 2015,
   Prague, Czech Republic.

#. B. Patzak, V. Smilauer: MuPIF reference manual 1.0.0, 2016. Available
   at `www.mupif.org <http://www.mupif.org/>`__

#. `Directorate-General for Research and Innovation (European
   Commission) <https://publications.europa.eu/en/publication-detail?p_p_id=portal2012documentDetail_WAR_portal2012portlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=maincontentarea&p_p_col_count=3&_portal2012documentDetail_WAR_portal2012portlet_javax.portlet.action=author&facet.author=RTD&language=en>`__,
   `What makes a material function? Let me compute the ways : modelling
   in H2020 LEIT-NMBP programme materials and nanotechnology projects -
   Study <https://bookshop.europa.eu/en/what-makes-a-material-function--pbKI0417104/>`__,
   ISBN: 978-92-79-63185-6 DOI: 10.2777/417118, 2017.

#. The European Materials Modelling Council, https://emmc.info/, 2017.

#. The Simplified Wrapper and Interface Generator (SWIG), https://swig.org/, 2023.

#. Boost.Python, a C++ library which enables seamless interoperability between C++ and the Python programming language, http://boostorg.github.io/python/doc/html/index.html, 2023.

#. pybind11 — Seamless operability between C++11 and Python, https://pybind11.readthedocs.io/en/stable/, 2023.


