import sys
sys.path.append('../../..')
import os
import socket

import conf
from mupif import Application
from mupif import PyroUtil

#nameserver app name
appname='ctu-server'

class local(Application.Application):
    """
    Mupif interface to Local dummy task

    """
    def __init__(self, file):
        super(local, self).__init__(file) #call basereturn
    def getApplicationSignature(self):
        return "CTU-server@"+ socket.gethostbyaddr(socket.gethostname())[0]+" version 1.0"

#create application
app = local("/dev/null")
# run the application server
appRecord = conf.apps['ctu-server']
PyroUtil.runAppServer(server=appRecord.serverName,
                      port=appRecord.remotePort,
                      nathost=conf.nathost, natport=appRecord.natPort,
                      nshost=conf.nshost, nsport=conf.nsport,
                      nsname=PyroUtil.getNSAppName(conf.jobname, appname), hkey=conf.hkey, app=app)




