import unittest
import mupif as mp
import numpy as np
import sys
import multiprocessing
import threading
import time
import Pyro5.api

#sys.excepthook=Pyro5.errors.excepthook
#Pyro5.config.DETAILED_TRACEBACK=True

class Heavydata_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
        cls.numGrains=2
        time.sleep(.5)
    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    # tests are run alphabetically (https://nose.readthedocs.io/en/latest/writing_tests.html)
    # we need to write the file before reading it back
    def test_01_write(self):
        C=self.__class__
        h5name=C.tmp+'/grain.h5'
        import time, random
        import astropy.units as u
        t0=time.time()
        atomCounter=0
        # precompiled schemas
        handle=mp.HeavyDataHandle(h5path=C.tmp+'/grain.h5',h5group='grains')
        grains=handle.makeRoot(schema='grain',schemasJson=mp.heavydata.sampleSchemas_json)
        grains.allocate(size=C.numGrains)
        sys.stderr.write(f"There is {len(grains)} grains.\n")
        for ig,g in enumerate(grains):
            if ig==0: C.grain_class=g.__class__
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
        C=self.__class__
        import time
        handle=mp.HeavyDataHandle(h5path=C.tmp+'/grain.h5',h5group='grains')
        grains=handle.readRoot()
        t0=time.time()
        atomCounter=0
        for g in grains:
            self.assertEqual(C.grain_class.__module__,g.__class__.__module__)
            self.assertEqual(C.grain_class.__name__,g.__class__.__name__)
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
    def test_03_publish(self):
        C=self.__class__
        handle=mp.HeavyDataHandle(h5path=C.tmp+'/grain.h5',h5group='grains')
        daemon=Pyro5.api.Daemon()
        C.uri=daemon.register(handle)
        # binary mode must be specified explicitly!
        # otherwise: remote UnicodeDecodeError somewhere, and then 
        # TypeError: a bytes-like object is required, not 'dict'
        handle.h5uri=str(daemon.register(mp.PyroFile(handle.h5path,mode='rb')))
        sys.stderr.write(f'Handle URI is {C.uri}, HDF5 URI is {handle.h5uri}\n')
        C.daemonRun=True
        C.daemonThread=threading.Thread(target=daemon.requestLoop,kwargs=dict(loopCondition=lambda: C.daemonRun))
        C.daemonThread.start()
    def test_04_consume(self):
        C=self.__class__
        try:
            proxy=Pyro5.api.Proxy(C.uri)
            # this MUST be called to get local instance of the handle
            # its constructor will download the HDF5 file, if the h5uri attribute is set
            local=proxy.getLocalCopy()
            sys.stderr.write(f'Local handle is a {local.__class__.__name__}\n')
            root=local.readRoot()
            sys.stderr.write(f'Proxied root has {len(root)} grains, {root.__class__}\n')
            self.assertEqual(C.numGrains,len(root))
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            raise
        finally:
            sys.stderr.write('Stopping daemon\n')
            C.daemonRun=False
            C.daemonThread.join()


