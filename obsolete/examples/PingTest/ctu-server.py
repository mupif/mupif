import sys
sys.path.append('../../..')
import os
import socket

import conf
from mupif import Model
from mupif import pyroutil

#nameserver app name
appname='ctu-server'

class local(model.Model):
    """
    Mupif interface to Local dummy task

    """
    def __init__(self, file):
        super(local, self).__init__(file) #call basereturn
    def getApplicationSignature(self):
        return "CTU-server@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"

#create application
app = local(os.devnull)
# run the application server
appRecord = [item for item in conf.apps if item[0] == appname][0]
pyroutil.runAppServer(server=appRecord[conf.appIndx_ServerName],
                      port=appRecord[conf.appIndx_RemotePort], 
                      nathost=conf.nathost, natport=appRecord[conf.appIndx_NATPort], 
                      nshost=conf.nshost, nsport=conf.nsport, 
                      appName=pyroutil.getNSAppName(conf.jobname, appname), hkey=conf.hkey, app=app)




