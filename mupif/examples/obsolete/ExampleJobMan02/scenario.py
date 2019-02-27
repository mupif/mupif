import clientConfig as cConf
import sys
sys.path.append('../../..')
from mupif import *
import logging
log = logging.getLogger()

import time as timeTime
start = timeTime.time()
log.info('Timer started')

# locate nameserver
ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)

# localize JobManager running on (remote) server and create a tunnel to it
# allocate the first application app1
appRec = None
try:
    appRec = PyroUtil.allocateApplicationWithJobManager(
        ns, cConf.demoJobManRec, cConf.jobNatPorts.pop(0), cConf.hkey,
        PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost)
    )
    app1 = appRec.getApplication()
except Exception as e:
    log.exception(e)
else:
    if app1 is not None:
        appsig = app1.getApplicationSignature()
        log.info("Working application 1 on server " + appsig)

        app1.solveStep(None)
        remoteFile = appRec.getJobManager().getPyroFile(appRec.getJobID(), 'test.txt')
        print(remoteFile)
        PyroUtil.uploadPyroFile("localtest.txt", remoteFile, cConf.hkey)

        file = open("localtest.txt", "r")
        answer = file.readlines()
        print(answer)

        if answer[0] == "Hello MMP!":
            print("Test OK")
        else:
            print("Test FAILED")
            sys.exit(1)


finally:
    if appRec is not None:
        appRec.terminateAll()


