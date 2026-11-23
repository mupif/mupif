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
import Pyro5.errors
import logging
import sys
import pickle
import time
import collections
import uuid
import warnings
from . import modelserverbase
from .modelserverbase import ModelServerBase, ModelServerStatus
from . import pyroutil
from .pyrofile import PyroFile
from .baredata import BareData
import os
import typing
import pydantic
import shutil
from typing import List

sys.excepthook = Pyro5.errors.excepthook
Pyro5.config.DETAILED_TRACEBACK = False

log = logging.getLogger(__name__)



@Pyro5.api.expose
class ModelServer (modelserverbase.ModelServerBase):
    """
    Simple job manager 2. 
    This implementation avoids the problem of GIL lock by running applicaton 
    server under new process with its own daemon.
    """
    from dataclasses import dataclass

    # ModelServer
    @dataclass
    class ActiveJob(object):
        proc: typing.Union[subprocess.Popen,multiprocessing.Process]
        uri: str
        starttime: float
        timeout: int
        user: str
        port: int
        jobLogName: str
        remoteLogUri: str

    ticketExpireTimeout = 10
    #: seconds allocateJob waits for a spawned job to report its URI; a job not ready by then is killed
    jobStartTimeout = 10
    #: seconds between two checks that the server is still registered in the nameserver (see
    #: pyroutil.watchRegistration); 0: not checked
    registrationCheckInterval = 30.
    #: preAllocate tickets work over Pyro (advertised as the nameserver tag ``mupif:tickets-v2``)
    remoteTickets = True

    def __init__(
            self,
            *,
            ns,
            appName,
            appClass,
            server=None,
            workDir=None,
            maxJobs=1,
            daemon=None,
            includeFiles=None,
            instance=None,
            # overrideNsPort=0
    ):
        """
        Constructor.

        See :func:`ModelServerBase.__init__`
        """
        super().__init__(appName=appName, workDir=workDir, maxJobs=maxJobs, instance=instance)
        self.ns = ns

        # pre-allocation tickets (see preAllocate): ticket (str) -> time.monotonic() when issued.
        # Before mupif:tickets-v2 tickets were uuid1 objects whose .time (100-ns ticks since 1582)
        # was compared with time.time(), so they never expired; and a ticket sent back over Pyro
        # arrived as a string and was not recognised, so every remote preAllocate leaked a slot.
        self.tickets: dict[str, float] = {}
        self.jobCounter = 0
        self.lock = threading.Lock()
        self.applicationClass = appClass
        self.server = server
        self.acceptingJobs = True
        self.includeFiles = includeFiles

        app = appClass()
        self.modelMetadata = app.getAllMetadata()

        threading.Thread(target=self._childMonitorLoop, daemon=True).start()

        log.debug('ModelServer: initialization done for application name %s' % self.applicationName)

    def __del__(self):
        # will cause the child monitoring thread to exit gracefully within 1 second
        # (or it dies with the main process, if that comes sooner)
        self._childMonitorFlag = False

    def runServer(self):
        return pyroutil.runJobManagerServer(jobman=self, ns=self.ns)

    class SpawnedProcessArgs(pydantic.BaseModel):
        """Args passed to child processes via Popen"""
        uriFileName: str
        nsUri: str
        appName: str
        jobID: str
        cwd: str
        appClass: object

        def pickle(self):
            # protocol=0 so that there are no NULLs
            return pickle.dumps(self.model_dump(), protocol=0)

        @classmethod
        def unpickle(cls, data): return cls(**pickle.loads(bytes(data, encoding='ascii')))

    @staticmethod
    def _spawnedProcessPopen():
        import sys
        # the process receives MUPIF_LOG_PYRO (URI) and MUPIF_LOG_PYRONAME (jobID); used at import time in mupif.util.setupLogginAtStartup
        import mupif # import eplicitly, though the unpickle would do it automatically as well
        args = ModelServer.SpawnedProcessArgs.unpickle(sys.argv[-1])
        log.info(f'New subprocess: nameserver {args.nsUri}, cwd {args.cwd}')
        os.chdir(args.cwd)
        app = args.appClass()
        app.setJobID(args.jobID)
        uri=mupif.pyroutil.runAppServer(
            app=app,
            appName=args.jobID,
            ns=Pyro5.api.Proxy(args.nsUri)
        )
        open(args.uriFileName+'~', 'w').write(str(uri))
        os.rename(args.uriFileName+'~', args.uriFileName)

    def __checkTicket(self, ticket):
        """
        Tell whether *ticket* is a valid (issued and not expired) pre-allocation ticket.

        Called with :attr:`lock` held. The ticket is compared as a string: tickets travel over Pyro,
        whose serializer turns a :class:`uuid.UUID` into a string (see :meth:`preAllocate`).
        """
        issued = self.tickets.get(str(ticket))
        return issued is not None and time.monotonic()-issued < ModelServer.ticketExpireTimeout

    def __getNumberOfActiveTickets(self):
        """
        Drop expired pre-allocation tickets and return the number of those left.

        Called with :attr:`lock` held (it changes :attr:`tickets`).
        """
        now = time.monotonic()
        for t in [t for t, issued in self.tickets.items() if now-issued >= ModelServer.ticketExpireTimeout]:
            del self.tickets[t]
        return len(self.tickets)

    def _updateActiveJobs(self):
        with self.lock:
            # take note of processes terminated asynchronously
            dead = []
            for jobId, job in self.activeJobs.items():
                if job.proc.poll() is None:
                    continue
                code = job.proc.returncode
                assert code is not None
                log.debug(f'Job {jobId} already finished, exit status {code}.')
                if code != 0:
                    log.error('Job {jobID} has non-zero exit status {code}')
                dead.append(jobId)
            for d in dead:
                self.doneJobs[d] = self.activeJobs[d]
                del self.activeJobs[d]

            for jobId, job in self.activeJobs.items():
                alive = time.time()-job.starttime
                if alive > job.timeout > 0:
                    log.error('Job {jobId}: alive for {alive} < timeout {timeout}: terminating.')
                    # don't call terminateJob directly: self.lock would deadlock
                    # instead terminate the process, this will be picked up above in later
                    job.proc.terminate()

    def _childMonitorLoop(self):
        self._childMonitorFlag = True
        while self._childMonitorFlag:
            time.sleep(1)
            self._updateActiveJobs()

    def getNumberOfFreeJobs(self):
        """Return the number of jobs which can be allocated now: free slots minus valid pre-allocation tickets."""
        with self.lock:
            return self.maxJobs - len(self.activeJobs) - self.__getNumberOfActiveTickets()

    def preAllocate(self, requirements=None):
        """
            Allows to pre-allocate(reserve) the resource. 
            Returns ticket id (as promise) to finally allocate resource. 
            The requirements is an optional job-man specific dictionary with 
            additional parameters (such as number of cpus, etc). 
            The returned ticket is valid only for fixed time period (suggest 10[s]), then should expire.
            Thread safe

            The ticket is a string (a UUID) valid for :attr:`ticketExpireTimeout` seconds; pass it
            to :meth:`allocateJob`. Servers whose tickets work over Pyro advertise the nameserver
            tag ``mupif:tickets-v2`` (older ones must not be sent preAllocate remotely: the ticket
            is never recognised nor expired there, and the slot is lost until restart).

            :return: the ticket, or None if there is no free slot
        """
        self._updateActiveJobs()
        with self.lock:
            prealocatedJobs = self.__getNumberOfActiveTickets()
            if (len(self.activeJobs) + prealocatedJobs) >= self.maxJobs:
                return None
            else:
                ticket = str(uuid.uuid4())
                self.tickets[ticket] = time.monotonic()
                return ticket

    def allocateJob(self, user, *, remoteLogUri=None, ticket=None): 
        """
        Allocates a new job.

        See :func:`JobManager.allocateJob`

        Modified to accept optional ticket for preallocated resource.
        Thread safe

        :except: unable to start a thread, no more resources

        """
        self._updateActiveJobs()
        if not self.acceptingJobs:
            raise RuntimeError('Not accepting any new jobs (soft-terminate has been called already).')
        with self.lock:
            log.info('allocateJob...')
            # allocate job if valid ticket given or available resource exist
            ntickets = self.__getNumberOfActiveTickets()
            validTicket = ticket and self.__checkTicket(ticket)
            if validTicket or ((len(self.activeJobs)+ntickets) < self.maxJobs):
                if validTicket:
                    del self.tickets[str(ticket)]  # the ticket is used up
                # update job counter
                self.jobCounter = self.jobCounter+1
                # the job registers itself in the nameserver under its jobID, so the ID must be unique
                # among all running model servers: use the registered (instance) name, not the base
                # name shared by all instances of this model server; for a single instance
                # registered under its base name this is the same as before ("N@appName")
                jobID = str(self.jobCounter)+"@"+self.getNSName()
                log.debug('trying to allocate '+jobID)
                # run the new application instance served by corresponding pyro daemon in a new process

                try:
                    targetWorkDir = self.getJobWorkDir(jobID)
                    log.info('checking target workdir %s', targetWorkDir)
                    if not os.path.exists(targetWorkDir):
                        os.makedirs(targetWorkDir)
                        log.info('creating target workdir %s', targetWorkDir)

                        if self.includeFiles:
                            for incF in self.includeFiles:
                                # copy
                                path_source = os.path.join(os.getcwd(), str(incF))
                                path_dest = os.path.join(targetWorkDir, str(incF))
                                shutil.copy(path_source, path_dest)

                except Exception as e:
                    log.exception(e)
                    raise
                    # return JOBMAN_ERR, None
                # the job process, once spawned: killed again if the allocation fails (see _discardJob)
                proc = None
                try:
                    args = ModelServer.SpawnedProcessArgs(
                        uriFileName=targetWorkDir+'/_mupif_uri',
                        nsUri=str(self.ns._pyroUri),
                        jobID=jobID,
                        cwd=targetWorkDir,
                        appName=self.applicationName,
                        appClass=self.applicationClass,
                    )
                    jobLogName = targetWorkDir+'/_mupif_job.log'
                    jobLog = open(jobLogName, 'w')
                    log.info(f'Logging into {jobLogName} (+ {remoteLogUri} remotely)')
                    # this env trickery add sys.path to PYTHONPATH so that if some module is only importable because of modified sys.path
                    # the subprocess will be able to import it as well
                    env = os.environ.copy()
                    env['PYTHONPATH'] = os.pathsep.join(sys.path)+((os.pathsep+env['PYTHONPATH']) if 'PYTHONPATH' in env else '')
                    # this will redirect logs the moment mupif is imported on the remote side
                    if remoteLogUri:
                        env['MUPIF_LOG_PYRO'] = remoteLogUri
                    # to be tuned?
                    env['MUPIF_LOG_LEVEL'] = 'DEBUG'
                    env['MUPIF_LOG_PROCESSNAME'] = f'{jobID}'
                    proc = subprocess.Popen([sys.executable, '-c', 'import mupif; mupif.ModelServer._spawnedProcessPopen()', '-', args.pickle()], stdout=jobLog, stderr=subprocess.STDOUT, env=env)
                    t0 = time.time()
                    tMax = self.jobStartTimeout
                    while time.time()-t0 < tMax:
                        if os.path.exists(args.uriFileName):
                            uri = open(args.uriFileName, 'r').read()
                            os.remove(args.uriFileName)
                            break
                        else:
                            time.sleep(.1)
                    else:
                        log.error('This is the subprocess log file contents: \n'+open(jobLogName, 'r').read())
                        raise RuntimeError(f'Timeout waiting {tMax}s for URI from spawned process'+(f' (process died meanwhile with exit status {proc.returncode})' if proc.poll() else '')+'. The process log inline follows:\n'+open(jobLogName, 'r').read())

                    log.info('Received URI: %s' % uri)
                    jobPort = int(uri.split(':')[-1])
                    log.info(f'Job runs on port {jobPort}')

                    # get model metadta remotely
                    model = Pyro5.api.Proxy(uri)
                    timeout = model.getMetadata('Timeout')
                except Exception as e:
                    log.exception(e)
                    # the job is not handed out nor recorded in activeJobs: nobody would ever
                    # terminate it, and it would keep running (and keep its nameserver entry)
                    self._discardJob(proc, jobID)
                    raise

                # check if uri is ok
                # either by doing some sort of regexp or query ns for it
                start = timeTime.time()
                self.activeJobs[jobID] = ModelServer.ActiveJob(proc=proc, starttime=start, timeout=timeout, user=user, uri=uri, port=jobPort, jobLogName=jobLogName, remoteLogUri=remoteLogUri)
                log.debug('ModelServer: new process ')
                log.debug(self.activeJobs[jobID])

                log.info('ModelServer:allocateJob: allocated ' + jobID)
                return modelserverbase.JOBMAN_OK, jobID, jobPort
            else:
                log.error(f'ModelServer: no more resources, activeJobs:{len(self.activeJobs)} + nTickets:{self.__getNumberOfActiveTickets()} >= maxJobs:{self.maxJobs}')
                raise modelserverbase.ModelServerNoResourcesException("ModelServer: no more resources")
                # return (JOBMAN_NO_RESOURCES,None)

    def _discardJob(self, proc, jobID):
        """
        Kill a job whose allocation failed, and remove its nameserver entry; never raises.

        allocateJob used to leave such a job running: e.g. a job which registered itself only after
        allocateJob had stopped waiting for it (jobStartTimeout) ran on, unknown to the server,
        with its nameserver entry, until killed by hand.

        :param proc: the job process (None if it was not spawned)
        :param jobID: the job's ID (its nameserver name)
        """
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(2)
            except subprocess.TimeoutExpired:
                log.warning(f'{jobID} still running 2 s after SIGTERM, killing it.')
                proc.kill()
                try:
                    proc.wait(2)
                except subprocess.TimeoutExpired:
                    log.error(f'{jobID} (pid {proc.pid}) did not end after SIGKILL')
        try:
            # job IDs are unique to this server instance (N@<registered name>), so the entry is the job's
            self.ns._pyroClaimOwnership()
            self.ns.remove(jobID)
        except Exception:
            log.exception(f'Could not remove {jobID} from the nameserver')

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
                    if isinstance(job.proc, multiprocessing.Process):
                        job.proc.terminate()
                        job.proc.join(2)
                        if job.proc.exitcode is None:
                            log.debug(f'{jobID} still running after 2s timeout, killing.')
                        job.proc.kill()
                        # delete entry in the list of active jobs
                    else:  # subprocess.Popen
                        job.proc.terminate()
                        try:
                            job.proc.wait(2)
                        except:
                            log.debug(f'{jobID} still running after 2s timeout, killing.')
                            job.proc.kill()
                    log.debug('ModelServer:terminateJob: job %s terminated' % jobID)
                    self.doneJobs[jobID] = job
                    del self.activeJobs[jobID]
                except KeyError:
                    log.debug('ModelServer:terminateJob: jobID error, job %s already terminated?' % jobID)
   
    def terminateAllJobs(self):
        """
        Terminates all registered jobs, frees the associated recources.
        """
        for key in self.activeJobs.copy():
            try:
                self.terminateJob(key)
            except Exception as e:
                log.debug("Can not terminate job %s" % key)

    def terminate(self, force=False):
        """
        Terminates job manager itself.
        """
        self._updateActiveJobs()
        self.acceptingJobs = False
        log.info('No more jobs will be accepted.')
        if not force and self.activeJobs:
            raise RuntimeError(f'There are {len(self.activeJobs)} active jobs; call terminate(force=True) to kill them.')
        nsName = self.getNSName()
        # stop watching the registration first, or it would register the server again
        if getattr(self, '_nsWatchStop', None) is not None:
            self._nsWatchStop.set()
        try:
            self.terminateAllJobs()
            self.ns._pyroClaimOwnership()
            # remove the entry of this instance only: another instance of the same model server
            # may have taken over the name meanwhile (see pyroutil.removeOwnRegistration)
            pyroutil.removeOwnRegistration(self.ns, nsName, self.pyroURI)
            log.debug("Removing job manager %s from a nameServer %s" % (nsName, self.ns))
        except Exception as e:
            log.exception(f"Can not remove job manager {nsName} from nameserver {self.ns}")
        if self.pyroDaemon:
            try:
                self.pyroDaemon.unregister(self)
            except Exception:
                pass
            if self.exclusiveDaemon:
                log.info("ModelServer:terminate Shutting down daemon %s" % self.pyroDaemon)
                try:
                    self.pyroDaemon.shutdown()
                except Exception:
                    pass
            self.pyroDaemon = None
        else:
            log.warning('Not terminating daemon since none assigned.')

    def getApplicationSignature(self):
        """
        See :func:`ModelServer.getApplicationSignature`
        """
        return 'Mupif.JobManager.ModelServer'


    def getStatus(self) -> List[ModelServerStatus.JobStatus]:
        self._updateActiveJobs()
        tnow = timeTime.time()
        with self.lock:
            return [ModelServerStatus.JobStatus(key=key,running=tnow-job.starttime,user=job.user,uri=job.uri,remoteLogUri=job.remoteLogUri) for key,job in self.activeJobs.items()]

    def getStatusExtended(self) -> ModelServerStatus:
        return ModelServerStatus(currJobs=self.getStatus(), totalJobs=self.jobCounter, maxJobs=self.maxJobs)

    def getModelMetadata(self):
        return self.modelMetadata

    def uploadFile(self, jobID, filename, pyroFile):
        """
        See :func:`JobManager.uploadFile`
        """
        targetFileName = self.jobManWorkDir+os.path.sep+jobID+os.path.sep+filename
        PyroFile.copy(targetFileName, pyroFile)

    def getLogFile(self, jobID):
        pf = PyroFile(filename=self.doneJobs[jobID].jobLogName, mode='rb', bufSize=2**20)
        self.pyroDaemon.register(pf)
        return pf
        # return self.getPyroFile(self.doneJobs[jobID].jobLogName)

    def getPyroFile(self, jobID, filename, mode="r", buffSize=2**20):
        """
        See :func:`JobManager.getPyroFile`
        """
        targetFileName = self.getJobWorkDir(jobID)+os.path.sep+filename
        log.info('ModelServer:getPyroFile ' + targetFileName)
        pfile = PyroFile(targetFileName, mode, buffSize)
        self.pyroDaemon.register(pfile)

        return pfile

class SimpleJobManager(ModelServer):
    def __init__(self, *args, **kwargs):
        warnings.warn("SimpleJobManager class was renamed to ModelServer — update your code.",DeprecationWarning)
        super().__init__(*args, **kwargs)
