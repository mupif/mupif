import mupif as mp
import sys, os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import model1

mp.SimpleJobManager(
    ns=mp.pyroutil.connectNameserver(),
    appClass=model1.Model1,
    appName='ex11-dist-m1',
).runServer()

