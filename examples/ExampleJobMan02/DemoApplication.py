from mupif import *

class DemoApplication (Application.Application):
    """
    Simple application
    """
    def __init__(self):
        pass

    def solveStep(self, tstep, stageID=0, runInBackground=False):

        file = open (self.workDir+"/test.txt", "w")
        file.write("Hello MMP!")
        file.close()

