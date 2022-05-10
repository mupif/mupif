import os
import sys
import logging
thisDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisDir+'/..')
import mupif as mp
logging.basicConfig(format='%(message)s')
log = logging.getLogger('run-ns')
log.setLevel(logging.DEBUG)


if __name__ == "__main__":
    nsBg = mp.pyroutil.runNameserverBg()
    log.warning(f"Starting nameserver on {nsBg.host}:{nsBg.port}")
    input("Press key to shutdown nameserver.")
