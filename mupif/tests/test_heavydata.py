import unittest
import mupif as mp
import numpy as np
import sys
import multiprocessing
import threading
import time
import Pyro5.api
import json
import time, random
import tempfile
import astropy.units as u

#sys.excepthook=Pyro5.errors.excepthook
#Pyro5.config.DETAILED_TRACEBACK=True

class Heavydata_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
        cls.numGrains=2
        time.sleep(.5)
    @classmethod
    def tearDownClass(cls):
        try: cls.tmpdir.cleanup()
        except: pass
        # this would fail under Windows:
        #  NotADirectoryError: [WinError 267] The directory name is invalid: 'C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\tmptwrsfaka\\grain.h5'

    # tests are run alphabetically (https://nose.readthedocs.io/en/latest/writing_tests.html)
    # we need to write the file before reading it back
    def test_01_write(self):
        C=self.__class__
        C.h5path=C.tmp+'/grain.h5'
        C.h5path2=C.tmp+'/grain2.h5'
        t0=time.time()
        atomCounter=0
        # precompiled schemas
        handle=mp.HeavyDataHandle(h5path=C.h5path,h5group='grains')
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
        # this is for checking the value later
        grains[0].getMolecules()[0].getAtoms()[0].getIdentity().setElement('Q')
        t1=time.time()
        sys.stderr.write(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).\n')

    def test_02_read(self):
        C=self.__class__
        handle=mp.HeavyDataHandle(h5path=C.h5path,h5group='grains')
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
    def test_03_daemon_start(self):
        C=self.__class__
        C.daemon=Pyro5.api.Daemon()
        C.daemonRun=True
        C.daemonThread=threading.Thread(target=C.daemon.requestLoop,kwargs=dict(loopCondition=lambda: C.daemonRun))
        C.daemonThread.start()
    def test_04_publish(self):
        C=self.__class__
        C.uri=C.daemon.register(handle:=mp.HeavyDataHandle(h5path=C.h5path,h5group='grains'))
        handle.exposeData()
        C.uri2=C.daemon.register(mp.HeavyDataHandle(h5path=C.h5path2,h5group='grains'))
        sys.stderr.write(f'Handle URI is {C.uri}, HDF5 URI is {handle.h5uri}\n')
    def test_05_read_local_copy(self):
        C=self.__class__
        try:
            proxy=Pyro5.api.Proxy(C.uri)
            # this MUST be called to get local instance of the handle
            # its constructor will download the HDF5 file, provided exposeData() had been called on the remote
            local=proxy.copyRemote()
            self.assertEqual(local.__class__,mp.heavydata.HeavyDataHandle)
            sys.stderr.write(f'Local handle is a {local.__class__.__name__}\n')
            root=local.readRoot()
            # sys.stderr.write(f'Local root has {len(root)} grains, {root.__class__}\n')
            self.assertEqual(C.numGrains,len(root))
            self.assertEqual(root[0].getMolecules()[0].getAtoms()[0].getIdentity().getElement(),'Q')
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_06_read_remote_proxy(self):
        C=self.__class__
        try:
            proxy=Pyro5.api.Proxy(C.uri)
            root=proxy.readRoot()
            self.assertEqual(root.__class__,Pyro5.api.Proxy)
            # special methods don't currently work with Pyro5, use __getitem__ instead of [] for now
            self.assertEqual(root.__getitem__(0).getMolecules().__getitem__(0).getAtoms().__getitem__(0).getIdentity().getElement(),'Q')
            a0id=root.__getitem__(0).getMolecules().__getitem__(0).getAtoms().__getitem__(0).getIdentity()
            self.assertRaises(KeyError,a0id.getAtomicMass) # Q is not a valid element
            # HDF5 is open read-only: "Unable to create group (no write intent on file)"
            # exceptiion type varies (h5py version?)
            self.assertRaises((OSError,ValueError),lambda: a0id.setElement('H')) 
            # self.assertEqual(a0id.getAtomicMass(),1)
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_07_write_remote_proxy(self):
        C=self.__class__
        try:
            t0=time.time()
            atomCounter=0
            # precompiled schemas
            handle=Pyro5.api.Proxy(C.uri2)
            grains=handle.makeRoot(schema='grain',schemasJson=mp.heavydata.sampleSchemas_json)
            grains.allocate(size=C.numGrains)
            sys.stderr.write(f"There is {grains.__len__()} grains.\n")
            #for ig,g in enumerate(grains):
            for ig in range(grains.__len__()):
                g=grains.__getitem__(ig)
                if ig==0: C.grain_class=g.__class__
                (molecules:=g.getMolecules()).allocate(size=random.randint(5,10))
                sys.stderr.write(f"Grain #{ig} has {g.getMolecules().__len__()} molecules\n")
                #for m in g.getMolecules():
                for im in range(molecules.__len__()):
                    m=molecules.__getitem__(im)
                    m.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
                    (atoms:=m.getAtoms()).allocate(size=random.randint(5,10))
                    #for a in m.getAtoms():
                    for ia in range(atoms.__len__()):
                        a=atoms.__getitem__(ia)
                        a.getIdentity().setElement(random.choice(['H','N','Cl','Na','Fe']))
                        a.getProperties().getTopology().setPosition((1,2,3)*u.nm)
                        a.getProperties().getTopology().setVelocity((24,5,77)*u.m/u.s)
                        struct=np.array([random.randint(1,20) for i in range(random.randint(5,20))],dtype='l')
                        a.getProperties().getTopology().setStructure(struct)
                        atomCounter+=1
            t1=time.time()
            sys.stderr.write(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).\n')
            # write and read back a single value
            grains.__getitem__(0).getMolecules().__getitem__(0).getAtoms().__getitem__(0).getIdentity().setElement('Q')
            self.assertEqual(grains.__getitem__(0).getMolecules().__getitem__(0).getAtoms().__getitem__(0).getIdentity().getElement(),'Q')
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_99_daemon_stop(self):
        C=self.__class__
        sys.stderr.write('Stopping daemon\n')
        C.daemonRun=False
        C.daemonThread.join()


