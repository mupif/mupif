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
#import logging
#logging.basicConfig(filename='jobman.log',filemode='w',level=logging.DEBUG)
#logger = logging.getLogger('jobman')

#error codes
JOBMAN_OK = 1
JOBMAN_NO_RESOURCES = 2
JOBMAN_ERR = 99


#
# TODO: 
#  - locking for thread safe operation (lock.
#    lock.acquire()
#    try:
#       ... access shared resource
#    finally:
#       lock.release() # release lock, no matter what
#
#  - how to kill the locked threads> this is an issue



class JobManager(object):
    """
    An abstract class representing simple job manager. 

    The purpose of the job manager is  following:
     - to allocate and register the new instance of application (called job)
     - to query the status of job
     - ro cancel the given job
     - to register its interface to pyro name server

    """
    def __init__ (self, appName, maxJobs=1):
        """
        Constructor. Initializes the receiver.

        ARGS:
        appName: name of application to be served
        """
        self.applicationName = appName
        self.maxJobs = maxJobs
        self.activeJobs = {}  # dictionary of active jobs

    def allocateJob (self, user):
        """
        Allocates the new instance of application.

        Returns:
            Returns tuple (errCode, jobID, port), where 
            errCode = (JOBMAN_OK, JOBMAN_ERR, JOBMAN_NO_RESOURCES)
            JOBMAN_OK indicates sucessfull allocation and JobID contains the pyro name, under which the new instance is registered 
                      (composed of application name and job number (allocated by jobmanager), ie, Miccress23)
            JOBMAN_ERR indicates an internal error
            JOBMAN_NO_RESOURCES job manager is not able to allocate new instance of application (no more recources available)
        """
        print('JobManager:allocateJob is abstract')
        return (JOBMAN_ERR,None)

    def terminateJob (self, jobID):
        """
        Terminates the given job, free the associated recources.

        ARGS:
            jobID (string):  jobID 
        Returns:
            JOBMAN_OK indicates sucessfull termination
            JOBMAN_ERR internal error
        """
    def getJobStatus (self, jobID):
        """
        Returns the status of the job. 

        ARGS:
            jobID (string): jobID
        Returns:
            
        """
    def getStatus (self):
        """
        """

    def uploadFile(self, jobID, filename):
        """
        Uploads the given file to application server, files are uploaded to dedicated jobID directory 
        Note:
            some support local code is needed to split the file and send individual chunks as buffers to remote server
        ARGS:
            jobID (string): jobID
            filename (string): path to file to upload)
        """
    def uploadFilePart(self, jobID, filePart, partID, eof=False):
        """
        """
    def dowloadFile(self, jobID, filename):
        """
        """



SJM_APP_INDX = 0
SJM_STARTTIME_INDX = 1
SJM_USER_INDX = 2

SJM2_PROC_INDX = 0
SJM2_URI_INDX = 3
SJM2_PORT_INDX = 4


"""
Simple job manager using Pyro thread pool based server. 
Requires Pyro servertype=thread pool based (SERVERTYPE config item). This is the default value.
For the thread pool server the amount of worker threads to be spawned is configured using THREADPOOL_SIZE 
config item (default value set to 16).

However, doe to GIL (Global Interpreter Lock of python the actual level of achievable concurency is low.
The threads created from a single python context are executed sequentilly. This implementation is
suitable only for servers with low workload.
"""
class SimpleJobManager(JobManager):
    
    def __init__ (self, daemon, ns, appAPIClass, appName, maxJobs=1):
        super(SimpleJobManager, self).__init__(appName, maxJobs)
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
        print('SimpleJobManager: initialization done')

    def allocateJob (self, user):

        self.lock.acquire()
        print ("SimpleJobManager:allocateJob...")
        if (len(self.activeJobs) >= self.maxJobs):
            print ("SimpleJobManager: no more resources")
            self.lock.release()
            return (JOBMAN_NO_RESOURCES,None)
        else:
            print ("haha")
            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            print ("SimpleJobManager: trying to allocate "+jobID)
            # run the new application instance in a new thread
            try:
                app = self.appAPIClass()
                app.registerPyro(self.daemon, self.ns)
                start = timeTime.time()
                self.activeJobs[jobID] = (app, start, user)
                #register agent
                uri = self.daemon.register(app)
                self.ns.register(jobID, uri)
                print ('NameServer %s registered uri %s' % (jobID, uri) )
                
            except:
                print "Unable to start thread"
                self.lock.release()
                raise
                return (JOBMAN_ERR,None)

            print ("SimpleJobManager:allocateJob: allocated " + jobID)
            self.lock.release()
            return (JOBMAN_OK, jobID, self.jobPort)

    def terminateJob (self, jobID):
        self.lock.acquire()
        self.activeJobs[jobID][SJM2_PROC_INDX].terminate()
        del self.activeJobs[jobID]
        print ("SimpleJobManager:terminateJob: job terminated " + jobID)
        self.lock.release()

    def getApplicationSignature(self):
        return "Mupif.JobManager.SimpleJobManager"

    def getStatus (self):
        """
        """
        status = []
        tnow = timeTime.time()
        for key in self.activeJobs:
            status.append((key, tnow-self.activeJobs[key][SJM_STARTTIME_INDX], self.activeJobs[key][SJM_USER_INDX] ))
        return status

class SimpleJobManager2 (JobManager):
    """
    Simple job manager. This implementation avoids the problem of GIL lock 
    by running applicaton server under new process with its own daemon. 
    """
    
    def __init__ (self, daemon, ns, appAPIClass, appName, ports, maxJobs=1):
        """
        ports: tuple containing ports to use (size of ports shuold be equal to maxJobs)
        """
        super(SimpleJobManager2, self).__init__(appName, maxJobs)
        # remember application API class to create new app instances later
        self.appAPIClass = appAPIClass
        self.daemon = daemon
        self.ns = ns
        self.jobCounter = 0
        self.freePorts = list(ports)
        if maxJobs > len(self.freePorts):
            print ("SimpleJobManager: not enough free ports, changing maxJobs to %d"%(self.freePorts.size()))
            self.maxJobs = len(self.freePorts)
        self.lock = threading.Lock()
        jobID = ""


        # Create a TCP/IP socket to get the data
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', 10000))
        self.s.listen(1)


        print('SimpleJobManager: initialization done')

    def allocateJob (self, user):

        self.lock.acquire()
        print ("SimpleJobManager:allocateJob...")
        if (len(self.activeJobs) >= self.maxJobs):
            print ("SimpleJobManager: no more resources")
            self.lock.release()
            return (JOBMAN_NO_RESOURCES,None)
        else:

            # update job counter
            self.jobCounter = self.jobCounter+1
            jobID = str(self.jobCounter)+"@"+self.applicationName
            print ("SimpleJobManager: trying to allocate "+jobID)
            # run the new application instance served by corresponding pyro daemon in a new process
            try:
                jobPort = self.freePorts.pop(0)
                print ("SimpleJobManager: port to be assigned %d"%(jobPort))

                proc = subprocess.Popen(["python", "JobMan2cmd.py", '-p', str(jobPort), '-j', jobID])
                print ("SimpleJobManager: new process has been started....")

                # try to get uri from subprocess
                conn, addr = self.s.accept()
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    if not data: break
                    uri = repr(data)
                    print ('Received uri: ', uri)
                conn.close()
                #s.shutdown(socket.SHUT_RDWR)
                #s.close()
                    
                # check if uri is ok
                # either by doing some sort of regexp or query ns for it
                start = timeTime.time()
                self.activeJobs[jobID] = (proc, start, user, uri, jobPort)
                print ("SimpleJobManager: new process ", self.activeJobs[jobID])
                
            except:
                print "Unable to start thread"
                self.lock.release()
                raise
                return (JOBMAN_ERR,None)

            print ("SimpleJobManager:allocateJob: allocated " + jobID)
            self.lock.release()
            return (JOBMAN_OK, jobID, jobPort)

    def terminateJob (self, jobID):
        self.lock.acquire()
        # unregister the applictaion from ns
        self.ns.remove(jobID)
        # terminate the process
        self.activeJobs[jobID][SJM2_PROC_INDX].terminate()
        
        # free the assigned port
        self.freePorts.append(self.activeJobs[jobID][SJM2_PORT_INDX])
        # delete entry in the list of active jobs
        print ("SimpleJobManager:terminateJob: job %s terminated, freeing port %d"%(jobID, self.activeJobs[jobID][SJM2_PORT_INDX]))
        del self.activeJobs[jobID]
        self.lock.release()

    def getApplicationSignature(self):
        return "Mupif.JobManager.SimpleJobManager"

    def getStatus (self):
        """
        """
        status = []
        tnow = timeTime.time()
        for key in self.activeJobs:
            status.append((key, tnow-self.activeJobs[key][SJM_STARTTIME_INDX], self.activeJobs[key][SJM_USER_INDX], self.activeJobs[key][SJM2_PORT_INDX]  ))
        return status
