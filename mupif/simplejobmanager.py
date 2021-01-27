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
import Pyro5
import logging
import sys
import time
import uuid 
from . import jobmanager
from . import pyroutil
from . import pyrofile
import os
import atexit

log=logging.getLogger(__name__)

try:
    import colorlog
    log.propagate=False
    handler=colorlog.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(colorlog.ColoredFormatter('%(asctime)s %(log_color)s%(levelname)s:%(filename)s:%(lineno)d %(message)s',datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(handler)
except ImportError: pass


# SimpleJobManager
SJM_APP_INDX = 0
SJM_STARTTIME_INDX = 1
SJM_USER_INDX = 2

# SimpleJobManager2
SJM2_PROC_INDX = 0  # object of subprocess.Popen
SJM2_URI_INDX = 3  # Pyro5 uri
SJM2_PORT_INDX = 4  # port
SJM2_TICKET_EXPIRE_TIMEOUT = 10 # ticket timeout



@Pyro5.api.expose
class SimpleJobManager2 (jobmanager.JobManager):
    """
    Simple job manager 2. 
    This implementation avoids the problem of GIL lock by running applicaton 
    server under new process with its own daemon.
    """
    def __init__(self, daemon, ns, appAPIClass, appName, portRange, jobManWorkDir, serverConfigPath, serverConfigFile, serverConfigMode, jobMan2CmdPath, maxJobs=1, jobMancmdCommPort=10000, overrideNsPort=0):
        """
        Constructor.

        See :func:`SimpleJobManager.__init__`
        :param tuple portRange: start and end ports for jobs which will be allocated by a job manager
        :param str serverConfigFile: path to serverConfig file
        :param str jobMan2CmdPath: path to JobMan2cmd.py
        :param int jobMancmdCommPort: optional communication port to communicate with jobman2cmd
        """
        super(SimpleJobManager2, self).__init__(appName, jobManWorkDir, maxJobs)
        # remember application API class to create new app instances later
        self.appAPIClass = appAPIClass
        self.daemon = daemon
        self.ns = ns

        self.tickets = [] # list of tickets issued when pre-allocating resources; tickets generated using uuid 
        self.jobCounter = 0
        self.jobMancmdCommPort = jobMancmdCommPort
        self.serverConfigPath = serverConfigPath
        self.configFile = serverConfigFile
        self.serverConfigMode = serverConfigMode
        self.jobMan2CmdPath = jobMan2CmdPath
        self.overrideNsPort = overrideNsPort
        self.freePorts = list(range(portRange[0], portRange[1]+1))
        if maxJobs > len(self.freePorts):
            log.error('SimpleJobManager2: not enough free ports, changing maxJobs to %d' % len(self.freePorts))
            self.maxJobs = len(self.freePorts)
        self.lock = threading.Lock()

        # Create a TCP/IP socket to get uri from daemon registering an application
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', self.jobMancmdCommPort))
        self.s.listen(1)

        #atexit.register(self.terminate)

        log.debug('SimpleJobManager2: initialization done for application name %s' % self.applicationName)

    def __checkTicket (self, ticket):
        """ Returns true, if ticket is valid, false otherwise"""
        currentTime = time.time()
        if (ticket in self.tickets):
            if (currentTime-ticket.time) < SJM2_TICKET_EXPIRE_TIMEOUT:
                return True
        return False

    def __getNumberOfActiveTickets(self):
        """
            Returns the number of active pre-allocation tickets. 
        """
        currentTime = time.time()
        for i in range(len(self.tickets) - 1, -1, -1):
            # check if ticket expired
            if (currentTime-self.tickets[i].time) > SJM2_TICKET_EXPIRE_TIMEOUT: 
                # remove it
                del(self.tickets[i])
        return len(self.tickets)

    def preAllocate (self, requirements=None): 
        """
            Allows to pre-allocate(reserve) the resource. 
            Returns ticket id (as promise) to finally allocate resource. 
            The requirements is an optional job-man specific dictionary with 
            additional parameters (such as number of cpus, etc). 
            The returned ticket is valid only for fixed time period (suggest 10[s]), then should expire.
            Thread safe
        """
        self.lock.acquire()
        prealocatedJobs = self.__getNumberOfActiveTickets()
        if (len(self.activeJobs) + prealocatedJobs) >= self.maxJobs:
            self.lock.release()
            return None
        else:
            ticket = uuid.uuid1()
            self.tickets.append(ticket)
            self.lock.release()
            return ticket


    def allocateJob(self, user, natPort, ticket=None): 
        """
        Allocates a new job.

        See :func:`JobManager.allocateJob`

        Modified to accept optional ticket for preallocated resource.
        Thread safe

        :except: unable to start a thread, no more resources

        """
        self.lock.acquire()
        log.info('SimpleJobManager2: allocateJob...')
        # allocate job if valid ticket given or available resource exist
        ntickets = self.__getNumberOfActiveTickets()
        validTicket = ticket and self.__checkTicket(ticket)
        if (validTicket) or ((len(self.activeJobs)+ntickets) < self.maxJobs):
            if (validTicket):
                self.tickets.remove(ticket) #remove ticket
            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            log.debug('SimpleJobManager2: trying to allocate '+jobID)
            # run the new application instance served by corresponding pyro daemon in a new process
            jobPort = self.freePorts.pop(0)
            log.info('SimpleJobManager2: port to be assigned %d' % jobPort)

            try:
                targetWorkDir = self.getJobWorkDir(jobID)
                log.info('SimpleJobManager2: Checking target workdir %s', targetWorkDir)
                if not os.path.exists(targetWorkDir):
                    os.makedirs(targetWorkDir)
                    log.info('SimpleJobManager2: creating target workdir %s', targetWorkDir)
            except Exception as e:
                log.exception(e)
                raise
                # return JOBMAN_ERR, None

            try:
                args = [self.jobMan2CmdPath, '-p', str(jobPort), '-j', str(jobID), '-n', str(natPort), '-d',
                        str(targetWorkDir), '-s', str(self.jobMancmdCommPort), '-i', self.serverConfigPath,  '-c',
                        str(self.configFile), '-m', str(self.serverConfigMode)]
                if self.overrideNsPort>0: args+=['--override-nsport',str(self.overrideNsPort)]
                if self.jobMan2CmdPath[-3:] == '.py':
                    # use the same python interpreter as running this code, prepend to the arguments
                    args.insert(0, sys.executable)
                    log.info("Using python interpreter %s" % sys.executable)
                    proc = subprocess.Popen(args)  # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                else:
                    proc = subprocess.Popen(args)  # stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                log.debug('SimpleJobManager2: new subprocess has been started: %s', " ".join(args))
            except Exception as e:
                log.exception(e)
                raise
                # return JOBMAN_ERR, None
            
            try:
                # try to get uri from Property.psubprocess
                uri = None  # avoids UnboundLocalError in py3k
                conn, addr = self.s.accept()
                log.debug('Connected by %s' % str(addr))
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    uri = repr(data).rstrip('\'').lstrip('\'')
                    log.info('Received uri: %s' % uri)
                conn.close()
                # s.shutdown(socket.SHUT_RDWR)
                # s.close()

                # check if uri is ok
                # either by doing some sort of regexp or query ns for it
                start = timeTime.time()
                self.activeJobs[jobID] = (proc, start, user, uri, jobPort)
                log.debug('SimpleJobManager2: new process ')
                log.debug(self.activeJobs[jobID])
            except Exception as e:
                log.exception(e)
                log.error('Unable to start thread')
                self.lock.release()
                raise
                # return JobManager.JOBMAN_ERR, None

            log.info('SimpleJobManager2:allocateJob: allocated ' + jobID)
            self.lock.release()
            return jobmanager.JOBMAN_OK, jobID, jobPort
        
        else:
            log.error('SimpleJobManager2: no more resources, activeJobs:%d >= maxJobs:%d' % (len(self.activeJobs), self.maxJobs))
            self.lock.release()
            raise jobmanager.JobManNoResourcesException("SimpleJobManager: no more resources")
            # return (JOBMAN_NO_RESOURCES,None)


    def terminateJob(self, jobID):
        """
        Terminates the given job, frees the associated recources.

        See :func:`JobManager.terminateJob`
        """
        self.lock.acquire()
        # unregister the application from ns
        self.ns._pyroClaimOwnership()
        self.ns.remove(jobID)
        # terminate the process
        if jobID in self.activeJobs:
            try:
                self.activeJobs[jobID][SJM2_PROC_INDX].terminate()
                try:
                    self.activeJobs[jobID][SJM2_PROC_INDX].wait(2)
                except subprocess.TimeoutExpired:
                    log.debug("SimpleJobManager2:terminateJob: jobID %s terminate wait timeout reached"%jobID)
                # free the assigned port
                self.freePorts.append(self.activeJobs[jobID][SJM2_PORT_INDX])
                # delete entry in the list of active jobs
                log.debug('SimpleJobManager2:terminateJob: job %s terminated, freeing port %d' % (
                    jobID, self.activeJobs[jobID][SJM2_PORT_INDX]))
                del self.activeJobs[jobID]
            except KeyError:
                log.debug('SimpleJobManager2:terminateJob: jobID error, job %s already terminated?' % jobID)
        self.lock.release()
   
    def terminateAllJobs(self):
        """
        Terminates all registered jobs, frees the associated recources.
        """
        for key in self.activeJobs.copy():
            try:
                self.terminateJob(key)
            except Exception as e:
                log.debug("Can not terminate job %s" % key)

    @Pyro5.api.oneway  # in case call returns much later than daemon.shutdown
    def terminate(self):
        """
        Terminates job manager itself.
        """
        try:
            self.terminateAllJobs()
            self.ns._pyroClaimOwnership()
            self.ns.remove(self.applicationName)
            log.debug("Removing job manager %s from a nameServer %s" % (self.applicationName, self.ns))
        except Exception as e:
            log.debug("Can not remove job manager %s from a nameServer %s" % (self.applicationName, self.ns))
        if self.daemon:
            try:
                self.daemon.unregister(self)
            except:
                pass
            log.info("SimpleJobManager2:terminate Shutting down daemon %s" % self.daemon)
            try:
                self.daemon.shutdown()
            except:
                pass
            self.daemon = None
        self.s.close()


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
            status.append((key, tnow-self.activeJobs[key][SJM_STARTTIME_INDX], self.activeJobs[key][SJM_USER_INDX],
                           self.activeJobs[key][SJM2_PORT_INDX]))
        return status

    def uploadFile(self, jobID, filename, pyroFile, hkey):
        """
        See :func:`JobManager.uploadFile`
        """
        targetFileName = self.jobManWorkDir+os.path.sep+jobID+os.path.sep+filename
        pyroutil.uploadPyroFile(targetFileName, pyroFile)

    def getPyroFile(self, jobID, filename, mode="r", buffSize=1024):
        """
        See :func:`JobManager.getPyroFile`
        """
        targetFileName = self.getJobWorkDir(jobID)+os.path.sep+filename
        log.info('SimpleJobManager2:getPyroFile ' + targetFileName)
        pfile = pyrofile.PyroFile(targetFileName, mode, buffSize)
        self.daemon.register(pfile)

        return pfile
