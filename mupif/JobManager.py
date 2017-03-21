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
from __future__ import absolute_import
from builtins import str, range, object

import threading
import subprocess
import socket
import time as timeTime
import Pyro4
import logging
from . import PyroFile
from . import PyroUtil
import os
logger = logging.getLogger()

#error codes
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

@Pyro4.expose
class JobManager(object):
    """
    An abstract (base) class representing a job manager. The purpose of the job manager is the following:

    * To allocate and register the new instance of application (called job)
    * To query the status of job
    * To cancel the given job
    * To register its interface to pyro name server

    .. automethod:: __init__
    """
    def __init__ (self, appName, jobManWorkDir, maxJobs=1):
        """
        Constructor. Initializes the receiver.

        :param str appName: Name of application
        :param str jobManWorkDir: Absolute path for storing data, if necessary
        :param int maxJobs: Maximum number of jobs to run simultaneously
        """
        self.applicationName = appName
        self.maxJobs = maxJobs
        self.activeJobs = {}  # dictionary of active jobs
        self.jobManWorkDir = jobManWorkDir

    def allocateJob (self, user, natPort):
        """
        Allocates a new job.

        :param str user: user name
        :param int natPort: NAT port used in ssh tunnel

        :return: tuple (error code, None). errCode = (JOBMAN_OK, JOBMAN_ERR, JOBMAN_NO_RESOURCES).             JOBMAN_OK indicates sucessfull allocation and JobID contains the PYRO name, under which the new instance is registered (composed of application name and a job number (allocated by jobmanager), ie, Miccress23). JOBMAN_ERR indicates an internal error, JOBMAN_NO_RESOURCES means that job manager is not able to allocate new instance of application (no more recources available)
        :rtype: tuple
        :except: JobManException when allocation of new job failed
        """
        logger.debug('JobManager:allocateJob is abstract')
        return (JOBMAN_ERR, None)

    def terminateJob (self, jobID):
        """
        Terminates the given job, frees the associated recources.

        :param str jobID: jobID
        :return: JOBMAN_OK indicates sucessfull termination, JOBMAN_ERR means internal error
        :rtype: str
        """
    def getJobStatus (self, jobID):
        """
        Returns the status of the job.

        :param str jobID: jobID
        """
    def getStatus (self):
        """
        """

    def uploadFile(self, jobID, filename, pyroFile):
        """
        Uploads the given file to application server, files are uploaded to dedicated jobID directory
        :param str jobID: jobID
        :param str filename: target file name
        :param PyroFile pyroFile: source pyroFile

        """

    def getPyroFile(self, jobID, filename, buffSize=1024):
        """
        Returns the (remote) PyroFile representation of given file.
        To create local copy of file represented by PyroFile, use PyroUtil.downloadPyroFile, see :func:`PyroUtil.downloadPyroFile`

        :param str jobID: job identifier (jobID)
        :param str filename: source file name (on remote server). The filename should contain only base filename, not a path, which is determined by jobManager based on jobID.
        :return: PyroFile representation of given file
        :rtype: PyroFile
        """

    def registerPyro(self, daemon, ns, uri, externalDaemon):
        """
        Possibility to register the Pyro daemon and nameserver.

        :param Pyro4.Daemon pyroDaemon: Optional pyro daemon
        :param Pyro4.naming.Nameserver pyroNS: Optional nameserver
        :param string PyroURI: Optional URI of receiver
        :param bool externalDaemon: Optional parameter when damon was allocated externally.
        """
        

#SimpleJobManager
SJM_APP_INDX = 0
SJM_STARTTIME_INDX = 1
SJM_USER_INDX = 2

#SimpleJobManager2
SJM2_PROC_INDX = 0 #object of subprocess.Popen
SJM2_URI_INDX = 3 #Pyro4 uri
SJM2_PORT_INDX = 4 #port

@Pyro4.expose
class SimpleJobManager(JobManager):
    """
    Simple job manager using Pyro thread pool based server.
    Requires Pyro servertype=thread pool based (SERVERTYPE config item). This is the default value.
    For the thread pool server the amount of worker threads to be spawned is configured using THREADPOOL_SIZE config item (default value set to 16).

    However, dee to GIL (Global Interpreter Lock of python the actual level of achievable concurency is low. The threads created from a single python context are executed sequentially. This implementation is suitable only for servers with a low workload.

    .. automethod:: __init__
    """
    def __init__ (self, daemon, ns, appAPIClass, appName, jobManWorkDir, maxJobs=1):
        """Constructor.

        :param Pyro4.Daemon daemon: running daemon for SimpleJobManager
        :param Pyro4.naming.Nameserver ns: running name server
        :param Application appAPIClass: application class
        :param str appName: application name
        :param str jobManWorkDir: see :func:`JobManager.__init__`
        :param int maxJobs: see :func:`JobManager.__init__`
        """
        super(SimpleJobManager, self).__init__(appName, jobManWorkDir, maxJobs)
        # remember application API class to create new app instances later
        self.appAPIClass = appAPIClass
        self.daemon = daemon
        self.ns = ns
        self.jobCounter = 0
        self.jobPort = daemon.locationString
        self.lock = threading.Lock()

        # pyro daemon running in thread pool based setting to allow for concurrent connections
        #self.pyroDaemon = Pyro4.Daemon(host=server, port=port, nathost=nathost, natport=natport)
        #self.pyroDaemon.requestLoop()
        #self.ns = connectNameServer(nshost, nsport, hkey)
        logger.debug('SimpleJobManager: initialization done')

    def allocateJob(self, user, natPort):
        """
        Allocates a new job.

        See :func:`JobManager.allocateJob`

        :except: unable to start a thread, no more resources
        """
        self.lock.acquire()
        logger.debug('SimpleJobManager:allocateJob...')
        if (len(self.activeJobs) >= self.maxJobs):
            logger.error('SimpleJobManager: no more resources')
            self.lock.release()
            raise JobManNoResourcesException("SimpleJobManager: no more resources");
            # return (JOBMAN_NO_RESOURCES,None)
        else:
            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            logger.debug('SimpleJobManager: trying to allocate '+jobID)
            # run the new application instance in a new thread
            try:
                app = self.appAPIClass()
                start = timeTime.time()
                self.activeJobs[jobID] = (app, start, user)
                #register agent; exposing all its methods
                #ExposedApp = Pyro4.expose(app)
                #uri = self.daemon.register(ExposedApp) #
                uri = self.daemon.register(app)
                self.ns.register(jobID, uri)
                logger.info('NameServer %s registered uri %s' % (jobID, uri) )

            except:
                logger.error('Unable to start thread')
                self.lock.release()
                raise
                return (JOBMAN_ERR,None)

            logger.info('SimpleJobManager:allocateJob: successfully allocated ' + jobID)
            self.lock.release()
            return (JOBMAN_OK, jobID, self.jobPort)

    def terminateJob (self, jobID):
        """
        Terminates the given job, frees the associated recources.

        See :func:`JobMSimpleJobManageranager.terminateJob`
        """
        self.lock.acquire()
        self.activeJobs[jobID][SJM2_PROC_INDX].terminate()
        del self.activeJobs[jobID]
        logger.debug('SimpleJobManager:terminateJob: job terminated ' + jobID)
        self.lock.release()

    def getApplicationSignature(self):
        """
        :return: application name
        :rtype: str
        """
        return "Mupif.JobManager.SimpleJobManager"

    def getStatus (self):
        """
        Returns a list of tuples for all running jobIDs
        :return: a list of tuples (jobID, running time, user)
        :rtype: a list of (str, float, str)
        """
        status = []
        tnow = timeTime.time()
        for key in self.activeJobs:
            status.append((key, tnow-self.activeJobs[key][SJM_STARTTIME_INDX], self.activeJobs[key][SJM_USER_INDX] ))
        return status


@Pyro4.expose
class SimpleJobManager2 (JobManager):
    """
    Simple job manager 2. This implementation avoids the problem of GIL lock by running applicaton server under new process with its own daemon.

    .. automethod:: __init__

    :param int jobMancmdCommPort: optional communication port to communicate with jobman2cmd
    :param str configFile: path to server config file

    """
    def __init__ (self, daemon, ns, appAPIClass, appName, portRange, jobManWorkDir, serverConfigPath, serverConfigFile, jobMan2CmdPath, maxJobs=1, jobMancmdCommPort=10000):
        """
        Constructor.

        See :func:`SimpleJobManager.__init__`
        :param tuple portRange: start and end ports for jobs which will be allocated by a job manager
        :param str serverConfigFile: path to serverConfig file
        :param str jobMan2CmdPath: path to JobMan2cmd.py
        """
        super(SimpleJobManager2, self).__init__(appName, jobManWorkDir, maxJobs)
        # remember application API class to create new app instances later
        self.appAPIClass = appAPIClass
        self.daemon = daemon
        self.ns = ns
        self.jobCounter = 0
        self.jobMancmdCommPort = jobMancmdCommPort
        self.serverConfigPath = serverConfigPath
        self.configFile = serverConfigFile
        self.jobMan2CmdPath = jobMan2CmdPath
        self.freePorts = list(range(portRange[0], portRange[1]+1))
        if maxJobs > len(self.freePorts):
            logger.error('SimpleJobManager2: not enough free ports, changing maxJobs to %d'%(self.freePorts.size()))
            self.maxJobs = len(self.freePorts)
        self.lock = threading.Lock()
        jobID = ""

        # Create a TCP/IP socket to get uri from daemon registering an application
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', self.jobMancmdCommPort))
        self.s.listen(1)

        logger.debug('SimpleJobManager2: initialization done')

    def allocateJob (self, user, natPort):
        """
        Allocates a new job.

        See :func:`JobManager.allocateJob`
        :except: unable to start a thread, no more resources
        """
        self.lock.acquire()
        logger.info('SimpleJobManager2:allocateJob...')
        if (len(self.activeJobs) >= self.maxJobs):
            logger.error('SimpleJobManager2: no more resources, activeJobs:%d >= maxJobs:%d' % (len(self.activeJobs), self.maxJobs) )
            self.lock.release()
            raise JobManNoResourcesException("SimpleJobManager: no more resources");
            # return (JOBMAN_NO_RESOURCES,None)
        else:
            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            logger.debug('SimpleJobManager2: trying to allocate '+jobID)
            # run the new application instance served by corresponding pyro daemon in a new process
            jobPort = self.freePorts.pop(0)
            logger.info('SimpleJobManager2: port to be assigned %d'%(jobPort))

            try:
                targetWorkDir = self.jobManWorkDir+os.path.sep+jobID
                logger.info('SimpleJobManager2: Checking target workdir %s', targetWorkDir)
                if not os.path.exists(targetWorkDir):
                    os.makedirs(targetWorkDir)
                    logger.info('SimpleJobManager2: creating target workdir %s', targetWorkDir)
            except Exception as e:
                logger.exception(e)
                raise
                return (JOBMAN_ERR,None)

            try:
                if self.jobMan2CmdPath[-3:] == '.py':
                    proc = subprocess.Popen(["python", self.jobMan2CmdPath, '-p', str(jobPort), '-j', jobID, '-n', str(natPort), '-d', str(targetWorkDir), '-s', str(self.jobMancmdCommPort), '-i', self.serverConfigPath, '-c', self.configFile])#, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                else:
                    proc = subprocess.Popen([self.jobMan2CmdPath, '-p', str(jobPort), '-j', jobID, '-n', str(natPort), '-d', str(targetWorkDir), '-s', str(self.jobMancmdCommPort), '-i', self.serverConfigPath, '-c', self.configFile])#, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                logger.debug('SimpleJobManager2: new subprocess has been started with JobMan2cmd.py')
            except Exception as e:
                logger.exception(e)
                raise
                return (JOBMAN_ERR,None)
            try:
                # try to get uri from Property.psubprocess
                uri = None # avoids UnboundLocalError in py3k
                conn, addr = self.s.accept()
                logger.debug('Connected by %s' % str(addr))
                while True:
                    data = conn.recv(1024)
                    if not data: break
                    uri = repr(data).rstrip('\'').lstrip('\'')
                    logger.info('Received uri: %s' % uri)
                conn.close()
                #s.shutdown(socket.SHUT_RDWR)
                #s.close()

                # check if uri is ok
                # either by doing some sort of regexp or query ns for it
                start = timeTime.time()
                self.activeJobs[jobID] = (proc, start, user, uri, jobPort)
                logger.debug('SimpleJobManager2: new process ')
                logger.debug(self.activeJobs[jobID])
            except Exception as e:
                logger.exception(e)
                logger.error('Unable to start thread')
                self.lock.release()
                raise
                return (JOBMAN_ERR,None)

            logger.info('SimpleJobManager2:allocateJob: allocated ' + jobID)
            self.lock.release()
            return (JOBMAN_OK, jobID, jobPort)

    def terminateJob(self, jobID):
        """
        Terminates the given job, frees the associated recources.

        See :func:`JobManager.terminateJob`
        """
        self.lock.acquire()
        # unregister the applictaion from ns
        self.ns.remove(jobID)
        # terminate the process
        self.activeJobs[jobID][SJM2_PROC_INDX].terminate()

        # free the assigned port
        self.freePorts.append(self.activeJobs[jobID][SJM2_PORT_INDX])

        # delete entry in the list of active jobs
        logger.debug('SimpleJobManager2:terminateJob: job %s terminated, freeing port %d'%(jobID, self.activeJobs[jobID][SJM2_PORT_INDX]))

        del self.activeJobs[jobID]
        self.lock.release()

    def getApplicationSignature(self):
        """
        See :func:`SimpleJobManager.getApplicationSignature`
        """
        return 'Mupif.JobManager.SimpleJobManager2'

    def getStatus(self):
        """
        See :func:`JobManager.getStatus`
        """
        status = []
        tnow = timeTime.time()
        for key in self.activeJobs:
            status.append((key, tnow-self.activeJobs[key][SJM_STARTTIME_INDX], self.activeJobs[key][SJM_USER_INDX], self.activeJobs[key][SJM2_PORT_INDX]  ))
        return status

    def uploadFile(self, jobID, filename, pyroFile):
        """
        See :func:`JobManager.uploadFile`
        """
        targetFileName = self.jobManWorkDir+os.path.sep+jobID+os.path.sep+filename
        PyroUtil.uploadPyroFile (targetFileName, pyroFile)

    def getPyroFile(self, jobID, filename, mode="r", buffSize=1024):
        """
        See :func:`JobManager.getPyroFile`
        """
        targetFileName = self.jobManWorkDir+os.path.sep+jobID+os.path.sep+filename
        logger.info('SimpleJobManager2:getPyroFile ' + targetFileName)
        pfile = PyroFile.PyroFile(targetFileName, mode, buffSize)
        self.daemon.register(pfile)

        return pfile
