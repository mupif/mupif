from __future__ import print_function
from builtins import str
import getopt, sys
import re
sys.path.append('..')
from mupif import *
import logging
logger = logging.getLogger()


import time as timeTime
start = timeTime.time()

#logger.info('Timer started')


def usage():
    print("Usage: nstest.py -n nshost -r nsPort [-k hkey]")
    print()
    print("nshost : hostname where nameserver is running")
    print("nsPort : port where nameserver listens")
    print("hkey : Pyro hkey")
    print("-d : turns debugging messages on")
    print() 


def main():

    nshost = None
    nsport = None
    hkey = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:r:k:d")
    except getopt.GetoptError as err:
        # print help information and exit:
        logger.exception(err)
        usage()
        sys.exit(2)
    
    debug = False
    
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
    
    except:
        # Exception as e:
        print("\n\nConnection to nameserfer failed\n")
        #logger.exception(e)
    else:
        print ("\n\nConnection to nameserver is OK\n")
        
if __name__ == '__main__':
    main()
