import unittest
import mupif as mp
import numpy as np
import sys
#from mupif.heavydata import HeavyDataHandle

class Heavydata_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    # tests are run alphabetically (https://nose.readthedocs.io/en/latest/writing_tests.html)
    # we need to write the file before reading it back
    def test_01_write(self):
        h5name=self.__class__.tmp+'/grain.h5'
        import time, random
        import astropy.units as u
        t0=time.time()
        atomCounter=0
        # precompiled schemas
        handle=mp.HeavyDataHandle(h5path=self.tmp+'/grain.h5',h5group='grains')
        grains=handle.makeRoot(schema='grain',schemasJson=mp.heavydata.sampleSchemas_json)
        grains.allocate(size=2)
        sys.stderr.write(f"There is {len(grains)} grains.\n")
        for ig,g in enumerate(grains):
            g.getMolecules().allocate(size=random.randint(5,15))
            sys.stderr.write(f"Grain #{ig} has {len(g.getMolecules())} molecules\n")
            for m in g.getMolecules():
                m.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
                m.getAtoms().allocate(size=random.randint(10,30))
                for a in m.getAtoms():
                    a.getIdentity().setElement(random.choice(['H','N','Cl','Na','Fe']))
                    a.getProperties().getTopology().setPosition((1,2,3)*u.nm)
                    a.getProperties().getTopology().setVelocity((24,5,77)*u.m/u.s)
                    struct=np.array([random.randint(1,20) for i in range(random.randint(5,20))],dtype='l')
                    a.getProperties().getTopology().setStructure(struct)
                    atomCounter+=1
        t1=time.time()
        sys.stderr.write(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).\n')

    def test_02_read(self):
        import time
        handle=mp.HeavyDataHandle(h5path=self.__class__.tmp+'/grain.h5',h5group='grains')
        grains=handle.readRoot()
        t0=time.time()
        atomCounter=0
        for g in grains:
            sys.stderr.write(f'Grain #{g.row} has {len(g.getMolecules())} molecules.\n')
            for m in g.getMolecules():
                m.getIdentity().getMolecularWeight()
                for a in m.getAtoms():
                    a.getIdentity().getElement()
                    a.getProperties().getTopology().getPosition()
                    a.getProperties().getTopology().getVelocity()
                    a.getProperties().getTopology().getStructure()
                    atomCounter+=1
        t1=time.time()
        sys.stderr.write(f'{atomCounter} atoms read in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).\n')


