import unittest,sys
sys.path.append('../..')
from mupif import *

class ParticleSet_TestCase(unittest.TestCase):
    def setUp(self):
        self.ps = particle.ParticleSet (id=ParticleSetID.PSID_ParticlePositions, size=5, xc=(0,1,2,3,4), yc=(1,2,3,4,5), zc=(2,3,4,5,6),attributes=dict(code=(10,11,12,13,14), colour=("red", "green", "gray", "black", "magenta")))
        self.ps1 = particle.ParticleSet (id=ParticleSetID.PSID_ParticlePositions, size=5, xc=(0,1,2,3,4), yc=(1,2,3,4,5), zc=(2,3,4,5,6), rvesize = 4, inclusionsize=0.5, attributes=dict(code=(10,11,12,13,14),colour=("red", "green", "gray", "black", "magenta")))

    def tearDown(self):
        self.ps=None

    def test_getParticle(self):
        self.assertEqual(self.ps.getParticle(0).num,0, 'error in getParticle')
        self.assertEqual(self.ps.getParticle(1).getPosition(),(1,2,3), 'error in getParticle')
        self.assertRaises(IndexError, self.ps.getParticle, 6)

    def test_getParticlePositions(self):
        self.assertEqual(self.ps.getParticlePositions(), ([0,1,2,3,4], [1,2,3,4,5], [2,3,4,5,6]), "getParticlePositions failed")
    
    def test_getParticleAttributes(self):
        self.assertEqual(self.ps.getParticleAttributes(), {'code':(10,11,12,13,14), 'colour':("red", "green", "gray", "black", "magenta")}, "getParticleAttributes failed")
    
    def test_getParticleAttribute(self):
        self.assertEqual(self.ps.getParticleAttribute('code'), (10,11,12,13,14), "getParticleAttribute failed")
        self.assertEqual(self.ps.getParticleAttribute('colour'), ("red", "green", "gray", "black", "magenta"), "getParticleAttribute failed")
        self.assertRaises(KeyError, self.ps.getParticleAttribute, 'hue')
    def test_getRveSize(self):
        self.assertEqual(self.ps.getRveSize(), 0, "getRVESize failed")
        self.assertEqual(self.ps1.getRveSize(), 4, "getRVESize failed")
    def test_getInclusionSize(self):
        self.assertEqual(self.ps.getInclusionSize(), 0, "getInclusionSize failed")
        self.assertEqual(self.ps1.getInclusionSize(), 0.5, "getInclusionSize failed")
    
class Particle_TestCase(unittest.TestCase):
    def setUp(self):
        self.ps = particle.ParticleSet (id=ParticleSetID.PSID_ParticlePositions, size=5, xc=(0,1,2,3,4), yc=(1,2,3,4,5), zc=(2,3,4,5,6), attributes=dict(code=(10,11,12,13,14), colour=("red", "green", "gray", "black", "magenta")))

    def tearDown(self):
        self.ps=None

    def test_getPosition(self):
        self.assertEqual(self.ps.getParticle(1).getPosition(),(1,2,3), 'error in getPosition')
        self.assertEqual(self.ps.getParticle(4).getPosition(),(4,5, 6), 'error in getPosition')
    
    def test_setPosition(self):
        self.ps.getParticle(0).setPosition((10,9,8))
        self.assertEqual(self.ps.getParticle(0).getPosition(),(10,9,8), 'error in setPosition')
    
    def test_getAttributes(self):
        self.assertEqual(self.ps.getParticle(0).getAttributes(), {'code':10, 'colour':"red"}, "error in getAttributes")
    
    def test_getAtttribute(self):
        self.assertEqual(self.ps.getParticle(0).getAttribute('code'), 10,  "error in getAttribute")
        self.assertEqual(self.ps.getParticle(1).getAttribute('colour'), "green", "error in getAttribute")
        self.assertRaises(KeyError, self.ps.getParticle(2).getAttribute, 'hue')

    
       


# python test_Metadata.py for stand-alone test being run
if __name__=='__main__': unittest.main()

 
