from builtins import str
import getopt, sys
sys.path.extend(['../..', '../examples'])
import Pyro4
from mupif import *
#from mupif import WorkflowMonitor
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


def formatLine(k,v,status):
    if isinstance(v, dict):
        if v.get('WorkflowMonitor.Status') == status:
            print ('{:30.30}|{:12.12}|{:3}%|{:20.20}|'.format(k,v.get('WorkflowMonitor.Status'), 
                                                        v.get('WorkflowMonitor.Progress'), 
                                                        v.get('WorkflowMonitor.Date')))

def main(nshost, nsport, hkey):

    
    print("hkey:"+cfg.hkey)
    print("Nameserver:"+cfg.nshost+":"+str(cfg.nsport))
    
    #locate nameserver
    
    ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
    #monitor = PyroUtil.connectApp(ns, 'monitor.MuPIF')

    monitorUri = ns.lookup('monitor.MuPIF')
    monitor = Pyro4.Proxy(monitorUri)
    data = monitor.getAllMetadata()
 
    print ('Monitor:'+str(monitorUri))
    print ("=======SCHEDULED=========")
    for k,v in data.items():
        formatLine(k,v, 'WorkflowMonitor.Initialized')

    print ("========RUNNING==========")
    for k,v in data.items():
        formatLine(k,v, 'WorkflowMonitor.Running')

    print ("========FINISHED=========")
    for k,v in data.items():
        formatLine(k,v, 'WorkflowMonitor.Finished')

    print ("========FAILED=========")
    for k,v in data.items():
        formatLine(k,v, 'WorkflowMonitor.Failed')

         
if __name__ == '__main__':

    mode = 3
    debug = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:r:k:m:d")
    except getopt.GetoptError as err:
        # print help information and exit:
        log.exception(err)
        usage()
        sys.exit(2)

    for o,a in opts:
        if o in ("-m"):
            #Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
            mode = int(a)

    cfg=config(mode)
    # get vars from config first
    nshost = cfg.nshost
    nsport = cfg.nsport
    hkey = cfg.hkey

    # override by commandline setting, if provided
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
            pass
        else:
            assert False, "unhandled option"

    if nshost == None or nsport == None:
        usage()
        sys.exit(2)


    main(nshost, nsport, hkey)
