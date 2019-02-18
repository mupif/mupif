# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import os
import Pyro4
from . import APIError
from . import MupifObject
from . import MValType
from .propertyID import PropertyID
from .fieldID import FieldID
from .functionID import FunctionID
from . import Property
from . import Field
from . import Function
from . import TimeStep
from .Physics import PhysicalQuantities as PQ

import logging
log = logging.getLogger()

MDTemplate = {  'Model.Model_ID' : MValType(1,(str,int) ),
                'Model.Model_name' : MValType(1,(str,) ),
                'Model.Model_description' : MValType(1,(str,) ),
                'Model.Model_time_lapse' : MValType(1,(PQ.PhysicalQuantity,) ),
                'Model.Model_publication' : MValType(0,(str,) ),
                'Model.Solver_name' : MValType(0,(str,) ),
                'Model.Solver_version_date' : MValType(0,(str,) ),
                'Model.Solver_license' : MValType(0,(str,) ),
                'Model.Solver_creator' : MValType(0,(str,) ),    
                'Model.Solver_language' : MValType(0,(str,) ),
                'Model.Solver_time_step' : MValType(0,(str,) ),
                'Model.Model_boundary_conditions' : MValType(0,(str,) ),
                'Model.Workflow_model_reference' : MValType(0,(str,) ),
                'Model.Accuracy' : MValType(0,(str,) ),
                'Model.Sensitivity' : MValType(0,(str,) ),
                'Model.Complexity' : MValType(0,(str,) ),
                'Model.Robustness' : MValType(0,(str,) ),
                'Model.Estimated_execution cost' : MValType(0,(float,) ),#EUR
                'Model.Estimated_personnel cost' : MValType(0,(float,) ),#working day
                'Model.Required_expertise' : MValType(0,(str,) ),
                'Model.Estimated_computational_time' : MValType(0,(PQ.PhysicalQuantity,) ),
                'Model.Inputs_and_relation_to_Data' : MValType(1,(list,) ),
                'Model.Outputs_and_relation_to_Data' : MValType(1,(list,) )
             }

@Pyro4.expose
class Application(MupifObject.MupifObject):
    """
    An abstract class representing an application and its interface (API).

    The purpose of this class is to define abstract services for data exchange and steering.
    This interface has to be implemented/provided by any application.
    The data exchange is performed by the means of new data types introduced in the framework,
    namely properties and fields. 
    New abstract data types (properties, fields) allow to hide all implementation details 
    related to discretization and data storage.

    .. automethod:: __init__
    """
    def __init__(self):
        """
        Constructor. Initializes the application.

        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        :param str executionID: Optional application execution ID (typically set by workflow)
        """
        super(Application, self).__init__()

        # mupif internals (do not change)
        self.pyroDaemon = None
        self.externalDaemon = False
        self.pyroNS = None
        self.pyroURI = None
        self.appName = None


    def initialize(self, file='', workdir='', executionID = None, metaData={}, **kwargs):
        """
        """
        self.metadata.update(metaData)
        self.printMetadata()

        # define futher app metadata 
        self.setMetadata('Model.ExecutionID', executionID)
        self.setMetadata('Model.Model_ID','2')
        self.setMetadata('Model.Model_name', self.getApplicationSignature())
        
        #self.printMetadata()
        #self.metadata.Model.Model_ID.aa=2000
        #print(self.metadata['Model']['Model_ID'])
        #print(self.metadata)
                
        self.file = file
        if workdir == '':
            self.workDir = os.getcwd()
        else:
            self.workDir = workdir
        
        self.validateMetadata(MDTemplate)
        

    def registerPyro(self, pyroDaemon, pyroNS, pyroURI, appName=None, externalDaemon = False):
        """
        Register the Pyro daemon and nameserver. Required by several services

        :param Pyro4.Daemon pyroDaemon: Optional pyro daemon
        :param Pyro4.naming.Nameserver pyroNS: Optional nameserver
        :param string pyroURI: Optional URI of receiver
        :param string appName: Optional application name. Used for removing from pyroNS
        :param bool externalDaemon: Optional parameter when daemon was allocated externally.
        """
        self.pyroDaemon = pyroDaemon
        self.pyroNS = pyroNS
        self.pyroURI = pyroURI
        self.appName = appName
        self.externalDaemon = externalDaemon

    def get(self, objectTypeID, time=None, objectID=0):
        """
        Returns the requested object at given time. Object is identified by id.

        :param PropertyID or FieldID or FunctionID objectTypeID: Identifier of the object
        :param Physics.PhysicalQuantity time: Target time
        :param int objectID: Identifies object with objectID (optional, default 0)

        :return: Returns requested object.
        """
        if isinstance(objectTypeID, PropertyID):
            return self.getProperty(objectTypeID, time, objectID)
        if isinstance(objectTypeID, FieldID):
            return self.getField(objectTypeID, time, objectID)
        if isinstance(objectTypeID, FunctionID):
            return self.getFunction(objectTypeID, time, objectID)
        return None

    def set(self, obj, objectID=0):
        """
        Registers the given (remote) object in application.

        :param Property.Property or Field.Field or Function.Function obj: Remote object to be registered by the application
        :param int objectID: Identifies object with objectID (optional, default 0)
        """
        if isinstance(obj, Property.Property):
            return self.setProperty(obj, objectID)
        if isinstance(obj, Field.Field):
            return self.setField(obj, objectID)
        if isinstance(obj, Function.Function):
            return self.setFunction(obj, objectID)

    def getField(self, fieldID, time, objectID=0):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        :param FieldID fieldID: Identifier of the field
        :param Physics.PhysicalQuantity time: Target time
        :param int objectID: Identifies field with objectID (optional, default 0)

        :return: Returns requested field.
        :rtype: Field
        """
    def getFieldURI(self, fieldID, time, objectID=0):
        """
        Returns the uri of requested field at given time. Field is identified by fieldID.

        :param FieldID fieldID: Identifier of the field
        :param Physics.PhysicalQuantity time: Target time
        :param int objectID: Identifies field with objectID (optional, default 0)

        :return: Requested field uri
        :rtype: Pyro4.core.URI
        """
        if self.pyroDaemon is None:
            raise APIError.APIError('Error: getFieldURI requires to register pyroDaemon in application')
        try:
            field = self.getField(fieldID, time, objectID=objectID)
        except:
            raise APIError.APIError('Error: can not obtain field')
        if hasattr(field, '_PyroURI'):
            return field._PyroURI
        else:
            uri = self.pyroDaemon.register(field)
            # inject uri into field attributes, note: _PyroURI is avoided
            # for deepcopy operation
            field._PyroURI = uri
            # self.pyroNS.register("MUPIF."+self.pyroName+"."+str(fieldID), uri)
            return uri

    def setField(self, field, objectID=0):
        """
        Registers the given (remote) field in application. 

        :param Field.Field field: Remote field to be registered by the application
        :param int objectID: Identifies field with objectID (optional, default 0)
        """
    def getProperty(self, propID, time, objectID=0):
        """
        Returns property identified by its ID evaluated at given time.

        :param PropertyID propID: property ID
        :param Physics.PhysicalQuantity time: Time when property should to be evaluated
        :param int objectID: Identifies object/submesh on which property is evaluated (optional, default 0)

        :return: Returns representation of requested property 
        :rtype: Property
        """
    def setProperty(self, property, objectID=0):
        """
        Register given property in the application

        :param Property.Property property: Setting property
        :param int objectID: Identifies object/submesh on which property is evaluated (optional, default 0)
        """
    def getFunction(self, funcID, time, objectID=0):
        """
        Returns function identified by its ID

        :param FunctionID funcID: function ID
        :param Physics.PhysicalQuantity time: Time when function should to be evaluated
        :param int objectID: Identifies optional object/submesh on which property is evaluated (optional, default 0)

        :return: Returns requested function
        :rtype: Function
        """
    def setFunction(self, func, objectID=0):
        """
        Register given function in the application.

        :param Function.Function func: Function to register
        :param int objectID: Identifies optional object/submesh on which property is evaluated (optional, default 0)
        """
    def getMesh (self, tstep):
        """
        Returns the computational mesh for given solution step.

        :param TimeStep.TimeStep tstep: Solution step
        :return: Returns the representation of mesh
        :rtype: Mesh
        """
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        """ 
        Solves the problem for given time step.

        Proceeds the solution from actual state to given time.
        The actual state should not be updated at the end, as this method could be 
        called multiple times for the same solution step until the global convergence
        is reached. When global convergence is reached, finishStep is called and then 
        the actual state has to be updated.
        Solution can be split into individual stages identified by optional stageID parameter. 
        In between the stages the additional data exchange can be performed.
        See also wait and isSolved services.

        :param TimeStep.TimeStep tstep: Solution step
        :param int stageID: optional argument identifying solution stage (default 0)
        :param bool runInBackground: optional argument, defualt False. If True, the solution will run in background (in separate thread or remotely).

        """
    def wait(self):
        """
        Wait until solve is completed when executed in background.
        """
    def isSolved(self):
        """
        Check whether solve has completed.

        :return: Returns true or false depending whether solve has completed when executed in background.
        :rtype: bool
        """ 
    def finishStep(self, tstep):
        """
        Called after a global convergence within a time step is achieved.

        :param TimeStep.TimeStep tstep: Solution step
        """
    def getCriticalTimeStep(self):
        """
        Returns a critical time step for an application.
        
        :return: Returns the actual (related to current state) critical time step increment
        :rtype: Physics.PhysicalQuantity
        """
    def getAssemblyTime(self, tstep):
        """
        Returns the assembly time related to given time step.
        The registered fields (inputs) should be evaluated in this time.

        :param TimeStep.TimeStep tstep: Solution step
        :return: Assembly time
        :rtype: Physics.PhysicalQuantity, TimeStep.TimeStep
        """
    def storeState(self, tstep):
        """
        Store the solution state of an application.

        :param TimeStep.TimeStep tstep: Solution step
        """
    def restoreState(self, tstep):
        """
        Restore the saved state of an application.
        :param TimeStep.TimeStep tstep: Solution step
        """
    def getAPIVersion(self):
        """
        :return: Returns the supported API version
        :rtype: str, int
        """
    def getApplicationSignature(self):
        """
        Get application signature.

        :return: Returns the application identification
        :rtype: str
        """
        return "Application"

    def removeApp(self, nameServer=None, appName=None):
        """
        Removes (unregisters) application from the name server.

        :param Pyro4.naming.Nameserver nameServer: Optional instance of a nameServer
        :param str appName: Optional name of the application to be removed
        """
        if nameServer is None:
            nameServer = self.pyroNS
        if appName is None:
            appName = self.appName
        
        if nameServer is not None:  # local application can run without a nameServer
            try:
                nameServer.remove(appName)
                log.debug("Removing application %s from a nameServer %s" % (appName, nameServer))
            except Exception as e:
                log.warning("Cannot remove application %s from nameServer %s" % (appName, nameServer))
                raise

    @Pyro4.oneway # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates the application. Shutdowns daemons if created internally.
        """
        # Remove application from nameServer
        # print("Removing")
        if self.pyroNS is not None:
            self.removeApp()
                        
        if self.pyroDaemon:
            self.pyroDaemon.unregister(self)
            log.info("Unregistering daemon %s" % self.pyroDaemon)
            # log.info(self.pyroDaemon)
            if not self.externalDaemon:
                self.pyroDaemon.shutdown()
            self.pyroDaemon=None

    def getURI(self):
        """
        :return: Returns the application URI or None if application not registered in Pyro
        :rtype: str
        """
        return self.pyroURI


@Pyro4.expose
class RemoteApplication (object):
    """
    Remote Application instances are normally represented by auto generated pyro proxy.
    However, when application is allocated using JobManager or ssh tunnel, the proper termination of the tunnel or job manager task is required.
    
    This class is a decorator around pyro proxy object represeting application storing the reference to job manager and related jobID or/and ssh tunnel.

    These extermal attributes could not be injected into Application instance, as it is remote instance (using proxy) and the termination of job and tunnel has to be done from local computer, which has the neccesary communication link established 
    (ssh tunnel in particular, when port translation takes place)
    """
    def __init__(self, decoratee, jobMan=None, jobID=None, appTunnel=None):
        self._decoratee = decoratee
        self._jobMan = jobMan
        self._jobID = jobID
        self._appTunnel = appTunnel
        
    def __getattr__(self, name):
        """ 
        Catch all attribute access and pass it to self._decoratee, see python data model, __getattr__ method
        """
        return getattr(self._decoratee, name)

    def getJobID(self):
        return self._jobID

    @Pyro4.oneway # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates the application. Terminates the allocated job at jobManager
        """
        if self._decoratee:
            self._decoratee.terminate()
            self._decoratee = None
        
        if self._jobMan and self._jobID:
            try:
                log.info("RemoteApplication: Terminating jobManager job %s on %s" % (str(self._jobID), self._jobMan.getNSName()))
                self._jobMan.terminateJob(self._jobID)
                self._jobID=None
            except Exception as e:
                print(e)
            finally:
                self._jobMan.terminateJob(self._jobID)
                self._jobID=None

        # close tunnel as the last step so an application is still reachable
        if self._appTunnel:
            # log.info ("RemoteApplication: Terminating sshTunnel of application")
            if self._appTunnel != "manual":
                self._appTunnel.terminate()

    def __del__(self):
        """
        Destructor, calls terminate if not done before.
        """
        self.terminate()
