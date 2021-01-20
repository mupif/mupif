import mupif
import time
import Pyro4

@Pyro4.expose
class testApp (mupif.model.Model):
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time.sleep (60*10)
