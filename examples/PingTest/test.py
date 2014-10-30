import sys
sys.path.append('../..')
import os
os.environ['PYRO_HMAC_KEY'] = "mmp-secret-key" #do not change 

from mupif import Application
from mupif import APIError
from mupif import PyroUtil
import time as timeTime
import conf

start = timeTime.time()
#locate nameserver
ns     = PyroUtil.connectNameServer('mech.fsv.cvut.cz', 9090)

results=[]
for apprecord in conf.apps:
    starti = timeTime.time()
    conf.logger.info("Trying to connect to server " + str(apprecord[conf.appIndx_Name]))
    tunnel = PyroUtil.sshTunnel(remoteHost=apprecord[conf.appIndx_ServerName], userName=apprecord[conf.appIndx_UserName], 
                                localPort=apprecord[conf.appIndx_NATPort], remotePort=apprecord[conf.appIndx_RemotePort],
                                sshClient=apprecord[conf.appIndx_SshClient])

    # connect to individual applications
    app = PyroUtil.connectApp(ns, PyroUtil.getNSAppName(conf.jobname, apprecord[conf.appIndx_Name]))
    if app:
        appsig=app.getApplicationSignature()
        msg = "Successfully connected to %-30s (%4.2f s)"%(appsig, timeTime.time()-starti)
        conf.logger.info(msg)
        conf.logger.info("Time elapsed %f s" % (timeTime.time()-starti) )
    else:
        msg = "Unable to connect to " + str(apprecord[conf.appIndx_Name])
        conf.logger.error(msg)
    if tunnel:
        tunnel.terminate()
    results.append(msg)


print ("=========SUMMARY============")
for r in results:
    print (r)


print ("Total time consumed %f s" % (timeTime.time()-start))
print ("Ping test finished")
