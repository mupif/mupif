import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 
os.environ['PYRO_LOGLEVEL'] = 'DEBUG'
os.environ['PYRO_LOGFILE'] = 'Pyro_log.txt'
import socket

from mupif import Application
from mupif import PyroUtil

# import basic definitions -> need to be customized
import conf
#set application name (used also as an index to apps dictionary defined in conf.py)
appname='micress'

class micress(Application.Application):
    """
    Mupif interface to micress (microstructure evolution simulation tool) 

    """
    def __init__(self, file):
        super(micress, self).__init__(file) #call base
        return
    def getApplicationSignature(self):
        return "Micress@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"



#create application
app = micress("/dev/null")
# run the application server
appRecord = conf.apps[appname]
PyroUtil.runAppServer(server=appRecord[conf.appIndx_ServerName], port=appRecord[conf.appIndx_RemotePort], 
                      nathost=conf.nathost, natport=appRecord[conf.appIndx_NATPort], 
                      nshost=conf.nshost, nsport=conf.nsport, 
                      nsname=PyroUtil.getNSAppName(conf.jobname, appname),app=app)
