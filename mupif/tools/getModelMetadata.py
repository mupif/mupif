from builtins import str
import getopt, sys
import re
sys.path.append('../..')
from mupif import *
import logging
log = logging.getLogger()
import json

import time as timeTime
start = timeTime.time()

#log.info('Timer started')


def usage():
    print("Usage: getModelMetadata.py -j jobmanname  -n nshost -r nsPort")
    print()
    print("jobmanname : jobmanname is the name under which the job manager is registered in pyro nameserver")
    print("nshost : hostname where nameserver is running")
    print("nsPort : port where nameserver listens")
    print("hkey : Pyro hkey")
    print("-d : turns debugging messages on")
    print() 


def main():

    nshost = '172.30.0.1'
    nsport = 9090
    hkey = 'mupif-secret-key'
    debug = False


    try:
        opts, args = getopt.getopt(sys.argv[1:], "j:n:r:td")
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage()
        sys.exit(2)
    
    jobmanname = None
    tunnel = False
    debug = False
    
    for o, a in opts:
        if o in ("-j"):
            jobmanname = a
        elif o in ("-n"):
            nshost = a
        elif o in ("-r"):
            nsport = int(a)
        elif o in ("-d"):
            debug = True
    
    
        else:
            assert False, "unhandled option"
    
    if jobmanname == None:
        usage()
        sys.exit(2)
    
    if not debug:
        log.setLevel("WARNING")
    
    print("hkey:"+hkey)
    print("Nameserver:"+nshost+":"+str(nsport))
    print("JobManager:"+jobmanname)
    
    
    #locate nameserver
    try:
        ns = pyroutil.connectNameServer(nshost=nshost, nsport=nsport, hkey=hkey)

        print ("=======JOB Managers=========")
        (uri, mdata) = ns.lookup(jobmanname, return_metadata=True)

        if (not uri):
            print ("JobManager "+jobmanname+" seems to be down")
        else:
            print (jobmanname+" is up, [uri:"+str(uri)+"]")
            hostname = None
            for val in mdata:                                                 
                match=re.match('host:(.+)', val)
                if (match):
                    hostname=match.group(1)
            if (hostname):

                jobMan = pyroutil.connectJobManager(ns, jobmanname, hkey=hkey)

                app = pyroutil.allocateApplicationWithJobManager(ns, jobMan, None, hkey)
                metadata = app.getAllMetadata()
                print (json.dumps(metadata))
            
                app.terminate()

                print("Time consumed %f s" % (timeTime.time()-start))

    except Exception as e:
        print("\nConnection to nameserfer failed\n")
        log.exception(e)
    else:
        print ("\nConnection to nameserver is OK\n")
        
if __name__ == '__main__':
    main()


