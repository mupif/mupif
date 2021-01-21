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
from builtins import str, range, object

import threading
import subprocess
import socket
import time as timeTime
import logging
import os
import Pyro5
log = logging.getLogger()

# error codes
JOBMAN_OK = 1
JOBMAN_NO_RESOURCES = 2
JOBMAN_ERR = 99

#
# TODO:
#  - locking for thread safe operation lock.acquire()
#    try:
#       ... access shared resource
#    finally:
#       lock.release() # release lock, no matter what
#
#  - how to kill the locked threads > this is an issue


class JobManException(Exception):
    """
    This class serves as a base class for exceptions thrown by the job manager.
    """
    pass


class JobManNoResourcesException(JobManException):
    """
    This class is thrown when there are no more available resources.
    """
    pass


@Pyro5.api.expose
class JobManager(object):
    """
    An abstract (base) class representing a job manager. The purpose of the job manager is the following:

    * To allocate and register the new instance of application (called job)
    * To query the status of job
    * To cancel the given job
    * To register its interface to pyro name server

    .. automethod:: __init__
    """
    def __init__(self, appName, jobManWorkDir, maxJobs=1):
        """
        Constructor. Initializes the receiver.

        :param str appName: Name of receiver (used also by NS)
        :param str jobManWorkDir: Absolute path for storing data, if necessary
        :param int maxJobs: Maximum number of jobs to run simultaneously
        """
        self.applicationName = appName
        self.maxJobs = maxJobs
        self.activeJobs = {}  # dictionary of active jobs
        self.jobManWorkDir = jobManWorkDir

    def preAllocate (self, requirements=None): 
        """
            Allows to pre-allocate(reserve) the resource. 
            Returns ticket id (as promise) to finally allocate resource. 
            The requirements is an optional job-man specific dictionary with 
            additional parameters (such as number of cpus, etc). 
            The returned ticket is valid only for fixed time period), then should expire.
        """
        return False
    def allocateJob(self, user, natPort, ticket=None):
        """
        Allocates a new job.

        :param str user: user name
        :param int natPort: NAT port used in ssh tunnel
        :ticket optional ticket for preallocated resource.

        :return: tuple (error code, None). errCode = (JOBMAN_OK, JOBMAN_ERR, JOBMAN_NO_RESOURCES). JOBMAN_OK indicates sucessfull allocation and JobID contains the PYRO name, under which the new instance is registered (composed of application name and a job number (allocated by jobmanager), ie, Miccress23). JOBMAN_ERR indicates an internal error, JOBMAN_NO_RESOURCES means that job manager is not able to allocate new instance of application (no more recources available)
        :rtype: tuple
        :except: JobManException when allocation of new job failed
        """
        log.debug('JobManager:allocateJob is abstract')
        return JOBMAN_ERR, None

    def terminateJob(self, jobID):
        """
        Terminates the given job, frees the associated recources.

        :param str jobID: jobID
        :return: JOBMAN_OK indicates sucessfull termination, JOBMAN_ERR means internal error
        :rtype: str
        """
    def terminate(self):
        """
        Terminates job manager itself.
        """

    def getJobStatus(self, jobID):
        """
        Returns the status of the job.

        :param str jobID: jobID
        """
    def getStatus(self):
        """
        """
    def getNSName(self):
        return self.applicationName

    def uploadFile(self, jobID, filename, pyroFile, hkey):
        """
        Uploads the given file to application server, files are uploaded to dedicated jobID directory
        :param str jobID: jobID
        :param str filename: target file name
        :param PyroFile pyroFile: source pyroFile
        :param str hkey: A password string
        """

    def getPyroFile(self, jobID, filename, buffSize=1024):
        """
        Returns the (remote) PyroFile representation of given file.
        To create local copy of file represented by PyroFile, use pyroutil.downloadPyroFile, see :func:`pyroutil.downloadPyroFile`

        :param str jobID: job identifier (jobID)
        :param str filename: source file name (on remote server). The filename should contain only base filename, not a path, which is determined by jobManager based on jobID.
        :param int buffSize:
        :return: PyroFile representation of given file
        :rtype: PyroFile
        """

    def registerPyro(self, daemon, ns, uri, appName, externalDaemon):
        """
        Possibility to register the Pyro daemon and nameserver.

        :param Pyro5.api.Daemon daemon: Optional pyro daemon
        :param Pyro4.naming.Nameserver ns: Optional nameserver
        :param string uri: Optional URI of receiver
        :param string appName:
        :param bool externalDaemon: Optional parameter when damon was allocated externally.
        """

    def getJobWorkDir(self, jobID):
        """
        Returns working directory of a job with given ID.

        :param str jobID:
        :return: job working directory
        :rtype: str
        """
        return self.jobManWorkDir + os.path.sep + jobID
        

class RemoteJobManager (object):
    """
    Remote jobManager instances are normally represented by auto generated pyro proxy.
    However, when ssh tunneled connection is established to connect to remote job manager, 
    its instance must be properly terminated.
    This class is a decorator around pyro proxy object represeting jobManager storing the
    reference to the ssh tunnel established.
    Note in case of VPN or direct (plain) connection, the plain Pyro proxy should be used.

    The attribute could not be injected into remote instance (using proxy) as the termination 
    has to be done from local computer, where the ssh tunnel has been created. 
    Also different connections (proxies) to the same jobManager can exist.
    """
    def __init__(self, decoratee, sshTunnel=None):
        self._decoratee = decoratee
        self._sshTunnel = sshTunnel
        
    def __del__(self):
        self.terminate()
        if self._sshTunnel:
            # log.info ("RemoteJobManager: autoterminating sshTunnel")
            # print ("RemoteJobManager: autoterminating sshTunnel")
            self._sshTunnel.terminate()
    
    @Pyro5.api.oneway  # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates the application. Terminates the allocated job at jobManager
        """
        if self._decoratee:
            # self._decoratee.terminate() #so far, leave the jobManager registered on nameserver
            self._decoratee = None

    def __getattr__(self, name):
        """ 
        Catch all attribute access and pass it to self._decoratee, see python data model, __getattar__ method
        """
        return getattr(self._decoratee, name)
