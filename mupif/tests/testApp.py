import mupif
import time
import Pyro5


@Pyro5.api.expose
class testApp (mupif.model.Model):
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time.sleep(60*10)
