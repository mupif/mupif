#!/usr/bin/env python

import sys
sys.path.append('../..')  # Path to mupif if installed locally

from builtins import str
import getopt
import sys
from mupif import JobManager
from mupif import pyroutil
from mupif import APIError

import logging
import time as timeTime
import curses
import re

global jobmanname
global host
jobid_col = 0
port_col = 35
user_col = 41
time_col = 70


def usage():
    print("Usage: jobManStatus -j jbmanname [-n nshost -r nsPort] [-k hkey] [-t -u user]")


def processor(win, jobman):
    global jobmanname
    global host

    win.erase()

    win.addstr(0, 0, "MuPIF Remote JobMan MONITOR")
    win.addstr(1, 0, jobmanname+" on "+host)
    win.hline(2, 0, '-', 80)
    win.addstr(3, jobid_col, "JobID")
    win.addstr(3, port_col, "Port")
    win.addstr(3, user_col, "user@host")
    win.addstr(3, time_col, "time")

    win.addstr(23, 0, "[q]uit")
    win.refresh()

    win1 = curses.newwin (10, 80, 5, 0)

    win.nodelay(1)
    while True:
        win.addstr(0, 70, timeTime.strftime("%H:%M:%S", timeTime.gmtime()))
        win.refresh()

        win1.erase()
        c = win.getch()
        if c == ord('q'):
            break
        status=jobman.getStatus()
        i = 0
        for rec in status:
            win1.addstr(i, jobid_col, rec[0])
            win1.addstr(i, port_col, str(rec[3]))
            win1.addstr(i, user_col, rec[2])
            mins = rec[1]//60
            hrs = mins//24
            mins = mins % 60
            sec = int(rec[1]) % 60
            jobtime = "%02d:%02d:%02d" % (hrs, mins, sec)
            win1.addstr(i, time_col, jobtime)
            i = i+1
        win1.refresh()
        timeTime.sleep(1)
    return


#######################################################################################


def main():
    global host
    global jobmanname
    nshost = '172.30.0.1'
    nsport = 9090
    hkey = 'mupif-secret-key'
    jobmanname = None
    debug = False
    # nshost = None
    ssh = False  # ssh flag (set to True if ssh tunnel need to be established)
    log = logging.getLogger()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:j:p:k:u:n:r:t")
        # print(opts, args)
    except getopt.GetoptError as err: 
        # print help information and exit: 
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    for o, a in opts:
        #        if o in ("-p"):
        #            port = int(a)
        #        elif o in ("-h"):
        #            host = a
        if o in ("-j",):
            jobmanname = a
        elif o in ("-k",):
            hkey = a
        elif o in ("-t",):
            ssh = True
        elif o in ("-u",):
            username = a
        elif o in ("-n",):
            nshost = a
        elif o in ("-r",):
            nsport = int(a)
        else:
            assert False, "unhandled option"
    
    # print("huhu:"+host+str(port))

    if not jobmanname:
        usage()
        sys.exit(2)

    # locate nameserver
    ns = pyroutil.connectNameServer(nshost, nsport, hkey)
    # locate remote jobManager application, request remote proxy
    jobManUri = ns.lookup(jobmanname)
    # get local port of jobmanager (from uri)
    jobmannatport = int(re.search(r'(\d+)$',str(jobManUri)).group(0))
    host = pyroutil.getIPfromUri(jobManUri)
    
    # extablish secure ssh tunnel connection
    if ssh:
        (host, jobmannatport, jobManNatHost, port) = pyroutil.getNSConnectionInfo(ns, jobmanname)
        tunnel = pyroutil.SshTunnel(
            remoteHost=host, userName=username, localPort=jobmannatport, remotePort=port, sshClient='ssh')
    
    jobMan = pyroutil.connectJobManager(ns, jobmanname, hkey=hkey)
  
    curses.wrapper(processor, jobMan)
    
    if ssh:
        tunnel.terminate()
        

    ###########################################################


if __name__ == '__main__':
    main()
