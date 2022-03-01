import mupif as mp
import sys, os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import model2

mp.SimpleJobManager(
    ns=mp.pyroutil.connectNameserver(),
    appClass=model2.Model2,
    appName='ex11-dist-m2',
).runServer()
