import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 

from mupif import Application
from mupif import PyroUtil


# import basic definitions -> need to be customized
import conf
#nameserver app name
appname='celsian'

class celsian(Application.Application):
    """
    Mupif interface to Celsian Computational Fluid Dynamics (CFD) tool

    """
    def __init__(self, file):
        super(celsian, self).__init__(file) #call basereturn
    def getApplicationSignature(self):
        return "Celsian@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"



#create application
app = celsian("/dev/null")
# run the application server
appRecord = [item for item in conf.apps if item[0] == appname][0]
PyroUtil.runAppServer(server=appRecord[conf.appIndx_ServerName], 
                      port=appRecord[conf.appIndx_RemotePort], 
                      nathost=conf.nathost, natport=appRecord[conf.appIndx_NATPort], 
                      nshost=conf.nshost, nsport=conf.nsport, 
                      nsname=PyroUtil.getNSAppName(conf.jobname, appname), app=app)




