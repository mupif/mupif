from __future__ import print_function
from builtins import str
import getopt, sys
import re
sys.path.append('../..')
from mupif import *
import logging
log = logging.getLogger()

import time as timeTime
start = timeTime.time()


def usage():
    print("Usage: nslist.py -n nshost -r nsPort [-k hkey]")
    print()
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
        opts, args = getopt.getopt(sys.argv[1:], "n:r:k:d")
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-k"):
            hkey = a
        elif o in ("-n"):
            nshost = a
        elif o in ("-r"):
            nsport = int(a)
        elif o in ("-d"):
            debug = True
    
        else:
            assert False, "unhandled option"
    
    if nshost == None or nsport == None:
        usage()
        sys.exit(2)
    
    print("hkey:"+hkey)
    print("Nameserver:"+nshost+":"+str(nsport))
    
    #locate nameserver
    try:
        ns = PyroUtil.connectNameServer(nshost=nshost, nsport=nsport, hkey=hkey)

        print ("=======JOB Managers=========")
        a = ns.list(metadata_any={PyroUtil.NS_METADATA_jobmanager}, return_metadata=True)
        for k,v in a.items():
            print ('{:30}:{}'.format(k,v))
        
        print ("=======Applications=========")
        a = ns.list(metadata_any={PyroUtil.NS_METADATA_appserver, 'appserver'}, return_metadata=True)
        for k,v in a.items():
            print ('{:30}:{}'.format(k,v))
    
    except Exception as e:
        print("\nConnection to nameserfer failed\n")
        log.exception(e)
    else:
        print ("\nConnection to nameserver is OK\n")
        
if __name__ == '__main__':
    main()
