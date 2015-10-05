from __future__ import print_function
from builtins import str
import sys
sys.path.append('../../..')
import os

import conf
from mupif import Application
from mupif import APIError
from mupif import PyroUtil
import time as timeTime


start = timeTime.time()
#locate nameserver
ns = PyroUtil.connectNameServer(conf.nshost, 9090, conf.hkey)

results=[]
tunnel= None
for apprecord in conf.apps:
    starti = timeTime.time()
    conf.logger.info("Trying to connect to server " + str(apprecord[conf.appIndx_Name]))

    #Find if we need different ssh server for authentication
    if apprecord[conf.appIndx_SshHost] == '':
        sshHost = apprecord[conf.appIndx_ServerName]
    else:
        sshHost = apprecord[conf.appIndx_SshHost]
    try:

        tunnel = PyroUtil.sshTunnel(remoteHost=apprecord[conf.appIndx_ServerName],
                                    userName=apprecord[conf.appIndx_UserName],
                                    localPort=apprecord[conf.appIndx_NATPort], remotePort=apprecord[conf.appIndx_RemotePort],
                                    sshClient=apprecord[conf.appIndx_SshClient], options=apprecord[conf.appIndx_Options],
                                    sshHost=sshHost)

        # connect to individual applications
        app = PyroUtil.connectApp(ns, PyroUtil.getNSAppName(conf.jobname, apprecord[conf.appIndx_Name]))
        if app:
            appsig=app.getApplicationSignature()
            msg = "Successfully connected to %-30s (%4.2f s)"%(appsig, timeTime.time()-starti)
            conf.logger.info(msg)
            conf.logger.info("Time elapsed %f s" % (timeTime.time()-starti) )
        else:
            msg = "Unable to connect to " + apprecord[conf.appIndx_Name]
            conf.logger.error(msg)
        results.append(msg)
    finally:
        conf.logger.debug("Closing ssh tunnel")
        if tunnel: tunnel.terminate()

print ("=========SUMMARY============")
for r in results:
    print (r)


print ("Total time consumed %f s" % (timeTime.time()-start))
print ("Ping test finished")
