import os
import sys
import logging
thisDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisDir+'/..')
import mupif as mp
logging.basicConfig(format='%(message)s')
log = logging.getLogger('run-ex')
log.setLevel(logging.DEBUG)


if __name__ == "__main__":
    nshost, nsport = mp.pyroutil.runNameserverBg()
    log.warning(f"Starting nameserver on {nshost}:{nsport}")
    input("Press key to shutdown nameserver.")
