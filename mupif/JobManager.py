# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
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
import threading
import subprocess
import socket
import time as timeTime
import Pyro4
import logging
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

    def uploadFile(self, jobID, filename):
        """
        Uploads the given file to application server, files are uploaded to dedicated jobID directory
        :param str jobID: jobID
        :param str filename: path to file to upload

        .. Note:: Some supporting local code is needed to split the file and send individual chunks as buffers to remote server.
        """
    def uploadFilePart(self, jobID, filePart, partID, eof=False):
        """
        Upload a piece of file to a jobID server

        ??

        """
    def dowloadFile(self, jobID, filename):
        """
        Download a file from a jobID server

        ??

        """

#SimpleJobManager
SJM_APP_INDX = 0
SJM_STARTTIME_INDX = 1
SJM_USER_INDX = 2

#SimpleJobManager2
SJM2_PROC_INDX = 0 #object of subprocess.Popen
SJM2_URI_INDX = 3 #Pyro4 uri
SJM2_PORT_INDX = 4 #port


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
            return (JOBMAN_NO_RESOURCES,None)
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
                #register agent
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

class SimpleJobManager2 (JobManager):
    """
    Simple job manager 2. This implementation avoids the problem of GIL lock by running applicaton server under new process with its own daemon.

    .. automethod:: __init__
    """
    def __init__ (self, daemon, ns, appAPIClass, appName, portRange, jobManWorkDir, maxJobs=1):
        """
        Constructor.

        See :func:`SimpleJobManager.__init__`
        :param tuple portRange: start and end ports for jobs which will be allocated by a job manager
        """
        super(SimpleJobManager2, self).__init__(appName, jobManWorkDir, maxJobs)
        # remember application API class to create new app instances later
        self.appAPIClass = appAPIClass
        self.daemon = daemon
        self.ns = ns
        self.jobCounter = 0
        self.freePorts = range(portRange[0], portRange[1]+1)
        if maxJobs > len(self.freePorts):
            logger.error('SimpleJobManager2: not enough free ports, changing maxJobs to %d'%(self.freePorts.size()))
            self.maxJobs = len(self.freePorts)
        self.lock = threading.Lock()
        jobID = ""

        # Create a TCP/IP socket to get uri from daemon registering an application
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', 10000))
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
            return (JOBMAN_NO_RESOURCES,None)
        else:
            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            logger.debug('SimpleJobManager2: trying to allocate '+jobID)
            # run the new application instance served by corresponding pyro daemon in a new process
            jobPort = self.freePorts.pop(0)
            logger.info('SimpleJobManager2: port to be assigned %d'%(jobPort))
            try:
                proc = subprocess.Popen(["python", "JobMan2cmd.py", '-p', str(jobPort), '-j', jobID, '-n', str(natPort), '-d', str(self.jobManWorkDir)])#, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                logger.debug('SimpleJobManager2: new subprocess has been started')
            except Exception as e:
                logger.exception(e)
                raise
                return (JOBMAN_ERR,None)
            try:
                # try to get uri from Property.psubprocess
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
        Uploads the given file to application server, files are uploaded to dedicated jobID directory
        :param str jobID: jobID
        :param str filename: path to file to upload

        .. Note:: Some supporting local code is needed to split the file and send individual chunks as buffers to remote server.
        """
        targetFileName = self.jobManWorkDir+"\"+jobID+"\"+filename
        PyroUtil.uploadPyroFile (targetFileName, pyroFile)

    def getPyroFile(self, jobID, filename):
        """
        Download a file from a jobID server

        ??

        """
        targetFileName = self.jobManWorkDir+"\"+jobID+"\"+filename
        return PyroFile.PyroFile(targetFileName, 'rb')
        
        
