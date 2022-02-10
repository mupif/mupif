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
from __future__ import annotations

import threading
import subprocess
import multiprocessing
import time as timeTime
import Pyro5
import logging
import sys
import time
import collections
import uuid 
from . import jobmanager
from . import pyroutil
from .pyrofile import PyroFile
import os
import typing

sys.excepthook = Pyro5.errors.excepthook
Pyro5.config.DETAILED_TRACEBACK = False

# spawn is safe for windows; this is a global setting
if multiprocessing.get_start_method() != 'spawn':
    multiprocessing.set_start_method('spawn', force=True)

log = logging.getLogger(__name__)

try:
    import colorlog
    log.propagate = False
    handler = colorlog.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(colorlog.ColoredFormatter('%(asctime)s %(log_color)s%(levelname)s:%(filename)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(handler)
except ImportError:
    pass


@Pyro5.api.expose
class SimpleJobManager (jobmanager.JobManager):
    """
    Simple job manager 2. 
    This implementation avoids the problem of GIL lock by running applicaton 
    server under new process with its own daemon.
    """
    from dataclasses import dataclass

    # SimpleJobManager
    @dataclass
    class ActiveJob(object):
        proc: typing.Union[subprocess.Popen,multiprocessing.Process]
        uri: str
        starttime: float
        user: str
        port: int

    ticketExpireTimeout = 10

    def __init__(
            self,
            *,
            ns,
            appName,
            appClass,
            server=None,
            nshost=None,
            nsport=None,
            workDir=None,
            maxJobs=1,
            daemon=None,
            # overrideNsPort=0
    ):
        """
        Constructor.

        See :func:`SimpleJobManager.__init__`
        """
        super().__init__(appName=appName, workDir=workDir, maxJobs=maxJobs)
        self.ns = ns

        self.tickets = []  # list of tickets issued when pre-allocating resources; tickets generated using uuid
        self.jobCounter = 0
        # self.overrideNsPort = overrideNsPort
        self.lock = threading.Lock()
        self.applicationClass = appClass
        self.server = server
        self.nshost = nshost
        self.nsport = nsport

        log.debug('SimpleJobManager: initialization done for application name %s' % self.applicationName)

    def runServer(self):
        return pyroutil.runJobManagerServer(jobman=self,ns=self.ns)


    @staticmethod
    def _spawnProcess(*, pipe, ns, appName, jobID, cwd, appClass):
        '''
        This function is called 
        '''
        # this is all run in the subprocess
        # log.info('Changing directory to %s',cwd)
        os.chdir(cwd)
        os.environ['MUPIF_LOG_LEVEL']='DEBUG'
        import mupif.pyroutil
        # sys.excepthook=Pyro5.errors.excepthook
        # Pyro5.config.DETAILED_TRACEBACK=True
        app = appClass()
        app.setJobID(jobID)
        uri = mupif.pyroutil.runAppServer(
            app=app,
            appName=jobID,
            ns=ns
        )
        pipe.send(uri)  # as bytes

    def __checkTicket(self, ticket):
        """ Returns true, if ticket is valid, false otherwise"""
        currentTime = time.time()
        if ticket in self.tickets:
            if (currentTime-ticket.time) < SimpleJobManager.ticketExpireTimeout:
                return True
        return False

    def __getNumberOfActiveTickets(self):
        """
            Returns the number of active pre-allocation tickets. 
        """
        currentTime = time.time()
        for i in range(len(self.tickets) - 1, -1, -1):
            # check if ticket expired
            if (currentTime-self.tickets[i].time) > SimpleJobManager.ticketExpireTimeout: 
                # remove it
                del(self.tickets[i])
        return len(self.tickets)


    def _updateActiveJobs(self):
        with self.lock:
            dead=[]
            for jobId,job in self.activeJobs.items():
                if job.proc.is_alive(): continue
                assert job.proc.exitcode is not None
                log.debug(f'Job {jobId} already finished, exit status {job.proc.exitcode}.')
                if job.proc.exitcode!=0: log.error('Job {jobID} has non-zero exit status {job.proc.exitcode}')
                dead.append(jobId)
            for d in dead: del self.activeJobs[d]


    def preAllocate(self, requirements=None):
        """
            Allows to pre-allocate(reserve) the resource. 
            Returns ticket id (as promise) to finally allocate resource. 
            The requirements is an optional job-man specific dictionary with 
            additional parameters (such as number of cpus, etc). 
            The returned ticket is valid only for fixed time period (suggest 10[s]), then should expire.
            Thread safe
        """
        self._updateActiveJobs()
        with self.lock:
            prealocatedJobs = self.__getNumberOfActiveTickets()
            if (len(self.activeJobs) + prealocatedJobs) >= self.maxJobs:
                return None
            else:
                ticket = uuid.uuid1()
                self.tickets.append(ticket)
                return ticket

    def allocateJob(self, user, ticket=None): 
        """
        Allocates a new job.

        See :func:`JobManager.allocateJob`

        Modified to accept optional ticket for preallocated resource.
        Thread safe

        :except: unable to start a thread, no more resources

        """
        self._updateActiveJobs()
        with self.lock:
            log.info('allocateJob...')
            # allocate job if valid ticket given or available resource exist
            ntickets = self.__getNumberOfActiveTickets()
            validTicket = ticket and self.__checkTicket(ticket)
            if validTicket or ((len(self.activeJobs)+ntickets) < self.maxJobs):
                if validTicket:
                    self.tickets.remove(ticket)  # remove ticket
                # update job counter
                self.jobCounter = self.jobCounter+1
                jobID = str(self.jobCounter)+"@"+self.applicationName
                log.debug('trying to allocate '+jobID)
                # run the new application instance served by corresponding pyro daemon in a new process

                try:
                    targetWorkDir = self.getJobWorkDir(jobID)
                    log.info('checking target workdir %s', targetWorkDir)
                    if not os.path.exists(targetWorkDir):
                        os.makedirs(targetWorkDir)
                        log.info('creating target workdir %s', targetWorkDir)
                except Exception as e:
                    log.exception(e)
                    raise
                    # return JOBMAN_ERR, None
                try:
                    parentPipe, childPipe = multiprocessing.Pipe()

                    kwargs = dict(
                        pipe=childPipe,
                        ns=self.ns,
                        jobID=jobID,
                        cwd=targetWorkDir,
                        appName=self.applicationName,
                        appClass=self.applicationClass,
                    )
                    proc = multiprocessing.Process(
                        target=SimpleJobManager._spawnProcess,
                        name=self.applicationName,
                        kwargs=kwargs
                    )
                    proc.start()
                    if not parentPipe.poll(timeout=10):
                        raise RuntimeError('Timeout waiting 10s for URI from spawned process.')
                    uri = parentPipe.recv()
                    log.info('Received URI: %s' % uri)
                    jobPort = int(uri.location.split(':')[-1])
                    log.info(f'Job runs on port {jobPort}')
                except Exception as e:
                    log.exception(e)
                    raise

                # check if uri is ok
                # either by doing some sort of regexp or query ns for it
                start = timeTime.time()
                self.activeJobs[jobID] = SimpleJobManager.ActiveJob(proc=proc, starttime=start, user=user, uri=uri, port=jobPort)
                log.debug('SimpleJobManager: new process ')
                log.debug(self.activeJobs[jobID])

                log.info('SimpleJobManager:allocateJob: allocated ' + jobID)
                return jobmanager.JOBMAN_OK, jobID, jobPort
            
            else:
                log.error(f'SimpleJobManager: no more resources, activeJobs:{len(self.activeJobs)} + nTickets:{self.__getNumberOfActiveTickets()} >= maxJobs:{self.maxJobs}')
                raise jobmanager.JobManNoResourcesException("SimpleJobManager: no more resources")
                # return (JOBMAN_NO_RESOURCES,None)

    def terminateJob(self, jobID):
        """
        Terminates the given job, frees the associated recources.

        See :func:`JobManager.terminateJob`
        """
        with self.lock:
            # unregister the application from ns
            self.ns._pyroClaimOwnership()
            self.ns.remove(jobID)
            # terminate the process
            if jobID in self.activeJobs:
                job = self.activeJobs[jobID]
                try:
                    job.proc.terminate()
                    job.proc.join(2)
                    if job.proc.exitcode is None:
                        log.debug(f'{jobID} still running after 2s timeout, killing.')
                    job.proc.kill()
                    # delete entry in the list of active jobs
                    log.debug('SimpleJobManager:terminateJob: job %s terminated' % jobID)
                    del self.activeJobs[jobID]
                except KeyError:
                    log.debug('SimpleJobManager:terminateJob: jobID error, job %s already terminated?' % jobID)
   
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
            log.exception(f"Can not remove job {self.applicationName} from nameserver {self.ns}")
        if self.pyroDaemon:
            try:
                self.pyroDaemon.unregister(self)
            except Exception:
                pass
            if not self.externalDaemon:
                log.info("SimpleJobManager:terminate Shutting down daemon %s" % self.pyroDaemon)
                try:
                    self.pyroDaemon.shutdown()
                except Exception:
                    pass
            self.pyroDaemon = None
        else:
            log.warning('Not terminating daemon since none assigned.')

    def getApplicationSignature(self):
        """
        See :func:`SimpleJobManager.getApplicationSignature`
        """
        return 'Mupif.JobManager.SimpleJobManager'

    def getStatus(self):
        """
        See :func:`JobManager.getStatus`
        """
        self._updateActiveJobs()
        JobManagerStatus = collections.namedtuple('JobManagerStatus', ['key', 'running', 'user'])
        status = []
        tnow = timeTime.time()
        with self.lock:
            for key in self.activeJobs:
                status.append(JobManagerStatus(key=key, running=tnow-self.activeJobs[key].starttime, user=self.activeJobs[key].user))
        return status

    def uploadFile(self, jobID, filename, pyroFile):
        """
        See :func:`JobManager.uploadFile`
        """
        targetFileName = self.jobManWorkDir+os.path.sep+jobID+os.path.sep+filename
        PyroFile.copy(targetFileName, pyroFile)
        # pyroutil.uploadPyroFile(targetFileName, pyroFile)

    def getPyroFile(self, jobID, filename, mode="r", buffSize=1024):
        """
        See :func:`JobManager.getPyroFile`
        """
        targetFileName = self.getJobWorkDir(jobID)+os.path.sep+filename
        log.info('SimpleJobManager:getPyroFile ' + targetFileName)
        pfile = PyroFile(targetFileName, mode, buffSize)
        self.pyroDaemon.register(pfile)

        return pfile
