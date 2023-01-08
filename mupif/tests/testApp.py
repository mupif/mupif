import mupif
import time
import Pyro5


@Pyro5.api.expose
class testApp (mupif.model.Model):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {'Name': 'Test Application', 'ID': 'mupif-tests-testApp'}
        super().__init__(metadata=metadata)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time.sleep(60*10)
