from __future__ import print_function
#Demo 20
import socket

socketNum = 9090
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
        s.settimeout(5)
        s.connect(('mech.fsv.cvut.cz', socketNum))
        print(socket.getdefaulttimeout())
        print ('mech.fsv.cvut.cz listens on socket %d' % socketNum)
        print('Closing socket %d' % socketNum)
        s.close()
except Exception as e:
        print('Exception type is %s' %e)
