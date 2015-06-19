import sys
sys.path.append('../..')

from mupif import Vertex

v = Vertex.Vertex(1,1,(10., 10., 0.))
print v.getCoordinates()
