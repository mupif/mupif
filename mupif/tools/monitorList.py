from builtins import str
import getopt, sys
import re
sys.path.extend(['../..', '../examples'])
import Pyro4
from mupif import *
import logging
log = logging.getLogger()
from Config import config


def usage():
    print("Usage: monitorlist.py -n nshost -r nsPort -m mode [-k hkey]")
    print()
    print("nshost : hostname where nameserver is running")
    print("nsPort : port where nameserver listens")
    print("hkey : Pyro hkey")
    print("-d : turns debugging messages on")
    print() 


def main():

    nshost = '127.0.0.1'
    nsport = 9090
    #hkey = 'mupif-secret-key'
    debug = False
    mode = 3

    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:r:k:m:d")
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
        elif o in ("-m"):
            #Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
            mode = int(a)
        else:
            assert False, "unhandled option"

    cfg=config(mode)


    if nshost == None or nsport == None:
        usage()
        sys.exit(2)
    
    print("hkey:"+cfg.hkey)
    print("Nameserver:"+cfg.nshost+":"+str(cfg.nsport))
    
    #locate nameserver
    
    ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
    #monitor = PyroUtil.connectApp(ns, 'monitor.MuPIF')

    monitorUri = ns.lookup('monitor.MuPIF')
    monitor = Pyro4.Proxy(monitorUri)
    print ('Monitor:'+str(monitorUri)+str(monitor))
    print ("=======ENTRIES=========")
    if (1):
        data = monitor.getAllMetadata()
        for k,v in data.items():
            print ('{:8}:{}'.format(k,v))
        
    #except Exception as e:
    #    print("\nConnection to nameserver failed\n")
    #    log.exception(e)
    #else:
    #    print ("\nConnection to nameserver is OK\n")
        
if __name__ == '__main__':
    main()
