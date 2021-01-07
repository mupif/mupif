from builtins import str
import getopt
import sys
import re
sys.path.append('../..')
from mupif import *
import logging
log = logging.getLogger()

import time as timeTime
start = timeTime.time()

# log.info('Timer started')


def usage():
    print("Usage: jobManTest.py -j jobmanname -h jobmanhost -p jobManport -n nshost -r nsPort [-k hkey] [-t -u user] [-d]")
    print()
    print("jobmanname : jobmanname is the name under which the job manager is registered in pyro nameserver")
    print("jobmanhost : hostname of the computer serving jibmanager (and application instances)")
    print("jobManport : port at which jobmanager deamon listens")
    print("nshost : hostname where nameserver is running")
    print("nsPort : port where nameserver listens")
    print("hkey : Pyro hkey")
    print("-t -u user: if -t provided, then ssh connection to jobmanager and application will be made using user as username")
    print("-d : turns debugging messages on")
    print() 


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "j:h:p:k:u:n:r:td")
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage()
        sys.exit(2)
    
    jobmanname = None
    tunnel = False
    debug = False
    hostname = None
    port = None
    hkey = ""
    nshost = ""
    nsport = 0
    username = ""
    
    for o, a in opts:
        if o in ("-j",):
            jobmanname = a
        elif o in ("-h",):
            hostname = a
        elif o in ("-p",):
            port = int(a)
        elif o in ("-k",):
            hkey = a
        elif o in ("-t",):
            tunnel = True
        elif o in ("-u",):
            username = a
        elif o in ("-n",):
            nshost = a
        elif o in ("-r",):
            nsport = int(a)
        elif o in ("-d",):
            debug = True

        else:
            assert False, "unhandled option"
    
    if jobmanname is None or hostname is None or port is None:
        usage()
        sys.exit(2)
    
    if not debug:
        log.setLevel("WARNING")
    
    print("hkey:"+hkey)
    print("Nameserver:"+nshost+":"+str(nsport))
    print("JobManager:"+jobmanname+"@"+hostname+":"+str(port))

    # locate nameserver
    ns = PyroUtil.connectNameServer(nshost=nshost, nsport=nsport, hkey=hkey)
    jobManUri = ns.lookup(jobmanname)
    print("Jobmanager uri:"+str(jobManUri))
    
    tunnelJobMan = None
    tunnelApp = None
    
    # get local port of jabmanager (from uri)
    jobmannatport = int(re.search('(\d+)$',str(jobManUri)).group(0))
    
    # create tunnel to JobManager running on (remote) server
    try:
        if tunnel:
            tunnelJobMan = PyroUtil.sshTunnel(remoteHost=hostname, userName=username, localPort=jobmannatport, remotePort=port, sshClient='ssh')
    except Exception as e:
        log.exception(e)
        tunnelJobMan.terminate()
    else:
        # connect to jobmanager
        jobMan = PyroUtil.connectJobManager(ns, jobmanname, hkey)
    
    try:
        (errCode, jobID, jobPort) = jobMan.allocateJob(PyroUtil.getUserInfo(), natPort=None)
        print("Application " + str(jobID) + " successfully allocted")
        if tunnel:
            tunnelApp = PyroUtil.sshTunnel(
                remoteHost=hostname, userName=username, localPort=6001, remotePort=jobPort, sshClient='ssh')
        app = PyroUtil.connectApp(ns, jobID, hkey)
        
        jobMan.terminateJob(jobID)
        if tunnelJobMan:
            tunnelJobMan.terminate()
        if tunnelApp:
            tunnelApp.terminate()
        
        print("Terminating " + str(jobID))
        print("Time consumed %f s" % (timeTime.time()-start))
    
    except Exception as e:
        print("test failed")
        log.exception(e)


if __name__ == '__main__':
    main()
