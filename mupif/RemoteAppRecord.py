class RemoteAppRecord (object):
    """
    Class keeping data on remote application connction, such as ssh tunnels, etc.
    """
    def __init__ (self, app, appTunnel, jobMan, jobManTunnel, jobID):
        """
        Constructor. Initializes the receiver
        :param Application app: application instance
        :param subprocess.Popen appTunnel: ssh tunnel subprocess representing ssh tunnel to application process
        :param JobManager jobMan: job manager instance that allocated application
        :param subprocess.Popen jobManTunnel: ssh tunnel subprocess representing ssh tunnel to jobManager
        :param string jobID: application jobID
        """
        self.app = app
        self.appTunnel = appTunnel
        self.jobMan = jobMan
        self.jobManTunnel = jobManTunnel
        self.jobID = jobID

    def getApplication(self):
        """
        :return: Instance of Application
        """
        return self.app

    def terminate(self):
        """
        Terminates the connection to remote application including ssh tunnels
        """
        if self.app: self.app.terminate()
        if self.jobMan: self.jobMan.terminateJob(self.jobID)
        if self.appTunnel: self.appTunnel.terminate()
        if self.jobManTunnel: self.jobManTunnel.terminate()
