class RemoteAppRecord (object):
    def __init__ (self, app, appTunnel, jobMan, jobManTunnel, jobID):
        self.app = app
        self.appTunnel = appTunnel
        self.jobMan = jobMan
        self.jobManTunnel = jobManTunnel
        self.jobID = jobID

    def getApplication(self):
        return self.app

    def terminate(self):
        if self.app: self.app.terminate()
        if self.jobMan: self.jobMan.terminateJob(self.jobID)
        if self.appTunnel: self.appTunnel.terminate()
        if self.jobManTunnel: self.jobManTunnel.terminate()
