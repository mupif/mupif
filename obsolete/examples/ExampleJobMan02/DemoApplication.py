import sys
sys.path.extend(['../../..'])
from mupif import *

class DemoApplication (model.Model):
    """
    Simple application
    """
    def __init__(self, file, workdir):
        super(DemoApplication, self).__init__(file, workdir)
        pass

    def solveStep(self, tstep, stageID=0, runInBackground=False):

        file = open (self.workDir+"/test.txt", "w")
        file.write("Hello MMP!")
        file.close()

    def getApplicationSignature(self):
        return "DemoApplication, ver 1.0"
