#!/usr/bin/env -S python3 -u
import subprocess
import os
import sys
import time
import atexit
import logging
thisDir = os.path.dirname(os.path.abspath(__file__))+'/..'
logging.basicConfig(format='%(message)s')
log = logging.getLogger('run-ex')
log.setLevel(logging.DEBUG)


def getExec():
    return tuple([sys.executable, '-u'])


def runBg(sleep=1):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([thisDir])
    bbg = [
        subprocess.Popen([*getExec(), thisDir+'/tools/nameserver.py'], bufsize=0, env=env)
    ]
    time.sleep(sleep)

    def bbgTerminate():
        for b in bbg:
            b.terminate()
        time.sleep(.5)
        for b in bbg:
            if b.returncode is None:
                b.kill()

    atexit.register(bbgTerminate)


if __name__ == "__main__":
    runBg()
    input("Press key to shutdown nameserver.")
