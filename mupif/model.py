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
import time
import copy
import logging
import Pyro5.api
import pydantic
from pydantic.dataclasses import dataclass
from typing import Optional, Any

from . import apierror
from . import data
from . import property
from . import field
from . import function
from . import timestep
from . import pyroutil
from . import pyrofile
from . import U
from .dataid import DataID
from . import meta


log = logging.getLogger()

prefix = "mupif."
type_ids = []
type_ids.extend(prefix+s for s in list(map(str, DataID)))


@Pyro5.api.expose
class Model(data.Process,extra='allow'):
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

    pyroDaemon: Optional[Any] = None
    exclusiveDaemon: bool = False
    pyroNS: Optional[str] = None
    pyroURI: Optional[str] = None
    appName: Optional[str] = None
    workDir: str = ''
    _jobID: Optional[str] = None

    metadata: Optional[meta.ModelMeta]=None

    def __init__(self, *, metadata: None|dict|meta.BaseMeta=None, **kw):
        super().__init__(**kw)

        (username, hostname) = pyroutil.getUserInfo()
        defaults = dict(
            Username=username,
            Hostname=hostname,
            Status='Instantiated',
            Date_time_start =time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            Execution = {'Status':'Instantiated'},
            Timeout = 0,  # no limit by default
        )
        # override defaults with user-provided metadata
        self.updateMetadata(meta._mergedDicts(defaults,metadata))


    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        """
        Initializes application, i.e. all functions after constructor and before run.

        :param str workdir: Optional parameter for working directory
        :param dict metadata: Optional dictionary used to set up metadata (can be also set by setMetadata() ).
        :param bool validateMetaData: Defines if the metadata validation will be called
        :param named_arguments kwargs: Arbitrary further parameters
        """
        self.updateMetadata(metadata)

        self.setMetadata('Name', self.getApplicationSignature())
        self.updateMetadata({'Execution':{'Status':'Initialized'}})

        if workdir == '':
            self.workDir = os.getcwd()
        else:
            self.workDir = workdir

        if validateMetaData:
            self.validateMetadata(meta.ModelMeta)
            # log.info('Metadata successfully validated')

    def updateAndPassMetadata(self, dictionary: dict):
        self.updateMetadata(md=dictionary)

    def registerPyro(self, *, daemon, ns, uri, appName=None, exclusiveDaemon=False, externalDaemon=None):
        """
        Register the Pyro daemon and nameserver. Required by several services

        :param Pyro5.api.Daemon pyroDaemon: Optional pyro daemon
        :param Pyro5.naming.Nameserver pyroNS: Optional nameserver
        :param string pyroURI: Optional URI of receiver
        :param string appName: Optional application name. Used for removing from pyroNS
        :param bool exclusiveDaemon: Optional parameter when daemon was allocated externally.
        """
        if externalDaemon is not None:
            import warnings
            warnings.warn('externalDaemon is deprecated, use exclusiveDaemon (with opposite meaning) instead',DeprecationWarning)
            exclusiveDaemon=not externalDaemon
        self.pyroDaemon = daemon
        self.pyroNS = ns
        self.pyroURI = uri
        self.appName = appName
        self.exclusiveDaemon = exclusiveDaemon

    def get(self, objectTypeID, time=None, objectID=""):
        """
        Returns the requested object at given time. Object is identified by id.

        :param DataID objectTypeID: Identifier of the object
        :param Physics.PhysicalQuantity time: Target time
        :param str objectID: Identifies object with objectID (optional, default 0)

        :return: Returns requested object.
        """

    def set(self, obj, objectID=""):
        """
        Registers the given (remote) object in application.

        :param property.Property or field.Field or function.Function or pyrofile.PyroFile or heavydata.HeavyDataHandle obj: Remote object to be registered by the application
        :param str objectID: Identifies object with objectID (optional, default 0)
        """

    def getFieldURI(self, fieldID, time, objectID=""):
        """
        Returns the uri of requested field at given time. Field is identified by fieldID.

        :param DataID fieldID: Identifier of the field
        :param Physics.PhysicalQuantity time: Target time
        :param str objectID: Identifies field with objectID (optional, default 0)

        :return: Requested field uri
        :rtype: Pyro5.api.URI
        """
        if self.pyroDaemon is None:
            raise apierror.APIError('Error: getFieldURI requires to register pyroDaemon in application')
        try:
            var_field = self.get(fieldID, time, objectID=objectID)
        except Exception:
            self.setMetadata('Status', 'Failed')
            raise apierror.APIError('Error: can not obtain field')
        if hasattr(var_field, '_PyroURI'):
            return var_field._PyroURI
        else:
            uri = self.pyroDaemon.register(var_field)
            # inject uri into var_field attributes, note: _PyroURI is avoided
            # for deepcopy operation
            var_field._PyroURI = uri
            # self.pyroNS.register("MUPIF."+self.pyroName+"."+str(fieldID), uri)
            return uri

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

        :param timestep.TimeStep tstep: Solution step
        :param int stageID: optional argument identifying solution stage (default 0)
        :param bool runInBackground: optional argument, defualt False. If True, the solution will run in background (in separate thread or remotely).

        """
        self.setMetadata('Status', 'Running')
        self.setMetadata('Progress', 0.)
        
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

        :param timestep.TimeStep tstep: Solution step
        """
        # print("Calling finishStep() of " + self.__class__.__name__)

    def getCriticalTimeStep(self):
        """
        Returns a critical time step for an application.
        
        :return: Returns the actual (related to current state) critical time step increment
        :rtype: Physics.PhysicalQuantity
        """
        return 10**10 * U.s

    def getAssemblyTime(self, tstep):
        """
        Returns the assembly time related to given time step.
        The registered fields (inputs) should be evaluated in this time.

        :param timestep.TimeStep tstep: Solution step
        :return: Assembly time
        :rtype: Physics.PhysicalQuantity, timestep.TimeStep
        """

    def storeState(self, tstep):
        """
        Store the solution state of an application.

        :param timestep.TimeStep tstep: Solution step
        """

    def restoreState(self, tstep):
        """
        Restore the saved state of an application.
        :param timestep.TimeStep tstep: Solution step
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
        return "Model"

    def removeApp(self, nameServer=None, appName=None):
        """
        Removes (unregisters) application from the name server.

        :param Pyro5.naming.Nameserver nameServer: Optional instance of a nameServer
        :param str appName: Optional name of the application to be removed
        """
        if nameServer is None:
            nameServer = self.pyroNS
        if appName is None:
            appName = self.appName
        
        if nameServer is not None:  # local application can run without a nameServer
            try:
                log.debug("Removing application %s from a nameServer %s" % (appName, nameServer))
                nameServer._pyroClaimOwnership()
                nameServer.remove(appName)
            except Exception as e:
                # log.warning("Cannot remove application %s from nameServer %s" % (appName, nameServer))
                log.exception(f"Cannot remove {appName} from {nameServer}?")
                # print("".join(Pyro5.errors.get_pyro_traceback()))
                self.setMetadata('Status', 'Failed')
                raise

    @Pyro5.api.oneway  # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates the application. Shutdowns daemons if created internally.
        """
        # print("Calling terminate() of " + self.__class__.__name__)
        self.setMetadata('Status', 'Finished')
        self.setMetadata('Date_time_end', time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        
        # Remove application from nameServer
        # print("Removing")
        if self.pyroNS is not None:
            self.removeApp()
                        
        if self.pyroDaemon:
            log.info(f"Unregistering from daemon {self.pyroDaemon}")
            self.pyroDaemon.unregister(self)
            if self.exclusiveDaemon: self.pyroDaemon.shutdown()
            self.pyroDaemon = None
        else:
            log.info("Terminating model") 

    def getURI(self):
        """
        :return: Returns the application URI or None if application not registered in Pyro
        :rtype: str
        """
        return self.pyroURI

    def printMetadata(self, nonEmpty=False):
        """
        Print all metadata
        :param bool nonEmpty: Optionally print only non-empty values
        :return: None
        :rtype: None
        """
        if self.hasMetadata('Name'):
            print('AppName:\'%s\':' % self.getMetadata('Name'))
        super().printMetadata(nonEmpty)

    def setJobID(self, jobid):
        self._jobID = jobid

    def getJobID(self):
        return self._jobID


@Pyro5.api.expose
class RemoteModel (object):
    """
    Remote Application instances are normally represented by auto generated pyro proxy.
    However, when application is allocated using JobManager or ssh tunnel, the proper termination of the tunnel or
    job manager task is required.
    
    This class is a decorator around pyro proxy object represeting application storing the reference to job manager and
    related jobID or/and ssh tunnel.

    These extermal attributes could not be injected into Application instance, as it is remote instance (using proxy)
    and the termination of job and tunnel has to be done from local computer, which has the neccesary
    communication link established (ssh tunnel in particular, when port translation takes place)
    """
    def __init__(self, decoratee, jobMan=None, jobID=None):
        self._decoratee = decoratee
        self._jobMan = jobMan
        self._jobID = jobID
        
    def __getattr__(self, name):
        """
        Catch all attribute access and pass it to self._decoratee, see python data model, __getattr__ method
        """
        return getattr(self._decoratee, name)

    def getJobID(self):
        return self._jobID
    
    @Pyro5.api.oneway  # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates the application. Terminates the allocated job at jobManager
        """
        if self._decoratee is not None:
            self._decoratee.terminate()
            self._decoratee = None
        
        if self._jobMan and self._jobID:
            try:
                log.info("RemoteApplication: Terminating jobManager job %s on %s" % (
                    str(self._jobID), self._jobMan.getNSName()))
                self._jobMan.terminateJob(self._jobID)
                self._jobID = None
            except Exception as e:
                print(e)
                self.setMetadata('Status', 'Failed')
            finally:
                self._jobMan.terminateJob(self._jobID)
                self._jobID = None

    def __del__(self):
        """
        Destructor, calls terminate if not done before.
        """
        self.terminate()
