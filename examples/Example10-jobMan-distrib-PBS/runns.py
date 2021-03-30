#!/usr/bin/env -S python3 -u
import subprocess, argparse, os, os.path, sys, time, typing, atexit, logging
thisDir=os.path.dirname(os.path.abspath(__file__))+'/..'
logging.basicConfig(format='%(message)s')
log=logging.getLogger('run-ex')
log.setLevel(logging.DEBUG)


def getExec():
    return tuple([sys.executable,'-u'])


def runBg(sleep=1):
    env=os.environ.copy()
    env['PYTHONPATH']=os.pathsep.join([thisDir+'/..',thisDir])
    bbg=[
        subprocess.Popen([*getExec(),thisDir+'/../tools/nameserver.py'],bufsize=0,env=env)
    ]
    time.sleep(sleep)
    def bbgTerminate():
        for b in bbg: b.terminate()
        time.sleep(.5)
        for b in bbg:
            if b.returncode is None: b.kill()

    atexit.register(bbgTerminate)

runBg()

input("Press key to shutdown nameserver.")


