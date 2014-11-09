import sys
sys.path.append('../..')
import os
import socket
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 

from mupif import Application
from mupif import PyroUtil

# import basic definitions -> need to be customized
import conf
#nameserver app name
appname='local'

class local(Application.Application):
    """
    Mupif interface to Local dummy task

    """
    def __init__(self, file):
        super(local, self).__init__(file) #call basereturn
    def getApplicationSignature(self):
        return "Local@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"

#create application
app = local("/dev/null")
# run the application server
appRecord = [item for item in conf.apps if item[0] == appname][0]
PyroUtil.runAppServer(server=appRecord[conf.appIndx_ServerName],
                      port=appRecord[conf.appIndx_RemotePort], 
                      nathost=conf.nathost, natport=appRecord[conf.appIndx_NATPort], 
                      nshost=conf.nshost, nsport=conf.nsport, 
                      nsname=PyroUtil.getNSAppName(conf.jobname, appname), app=app)




