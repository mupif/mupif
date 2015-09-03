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
for apprecord in conf.apps.values():
    starti = timeTime.time()
    conf.logger.info("Trying to connect to server " + str(apprecord.name))

    #Find if we need different ssh server for authentication
    if apprecord.sshHost == '':
        sshHost = apprecord.serverName
    else:
        sshHost = apprecord.sshHost

    try:
        tunnel = PyroUtil.sshTunnel(remoteHost=apprecord.serverName,
                                    userName=apprecord.userName,
                                    localPort=apprecord.natPort, remotePort=apprecord.remotePort,
                                    sshClient=apprecord.sshClient, options=apprecord.options,
                                    sshHost=sshHost)

        # connect to individual applications
        app = PyroUtil.connectApp(ns, PyroUtil.getNSAppName(conf.jobname, apprecord.name))
        if app:
            appsig=app.getApplicationSignature()
            msg = "Successfully connected to %-30s (%4.2f s)"%(appsig, timeTime.time()-starti)
            conf.logger.info(msg)
            conf.logger.info("Time elapsed %f s" % (timeTime.time()-starti) )
        else:
            msg = "Unable to connect to " + str(apprecord.name)
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
