import sys
sys.path.append('../../..')
import os
import socket

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
appRecord = conf.apps['celsian']
PyroUtil.runAppServer(server=appRecord.serverName, 
                      port=appRecord.remotePort, 
                      nathost=conf.nathost, natport=appRecord.natPort, 
                      nshost=conf.nshost, nsport=conf.nsport, 
                      nsname=PyroUtil.getNSAppName(conf.jobname, appname), hkey=conf.hkey, app=app)




