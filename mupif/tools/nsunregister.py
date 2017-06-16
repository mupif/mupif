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
    print("Usage: nsunregister.py -n nshost -r nsPort [-k hkey] -i itemName -a")
    print()
    print("nshost : hostname where nameserver is running")
    print("nsPort : port where nameserver listens")
    print("hkey : Pyro hkey")
    print("itemName : name of job manager or application to be removed")
    print("-a : remove all job managers and applications")
    print("-d : turns debugging messages on")
    print() 


def main():

    nshost = '172.30.0.1'
    nsport = 9090
    hkey = 'mupif-secret-key'
    itemName = ''
    debug = False
    removeAll = False
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:r:k:d:i:a")
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
        elif o in ("-all"):
            removeAll = True
        elif o in ("-i"):
            itemName = a    
    
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
        a = ns.list(return_metadata=True)
        
    except:
        # Exception as e:
        print("\nConnection to nameserver failed\n")
        #log.exception(e)
    else:
        print ("\nConnection to nameserver is OK\n")   
        
        
    if removeAll:
        for k,v in a.items():
            ns.remove(k)
    
    if itemName:
        if itemName in a.keys():
            ns.remove(itemName)
        else:
            print("Item %s is not registered on the name server, giving list of applications" % itemName)
            for key, value in a.iteritems():
                print(key, value)
            
   
        
if __name__ == '__main__':
    main()
