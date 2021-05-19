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
        # precompiled schemas
        for handle in [
                mp.HeavyDataHandle(h5path=C.h5path,h5group='test',mode='create',schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json),
                mp.HeavyDataHandle(mode='create-memory',schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
            ]:
            t0=time.time()
            atomCounter=0
            with handle as grains:
                grains.resize(size=C.numGrains)
                sys.stderr.write(f"There is {len(grains)} grains.\n")
                for ig,g in enumerate(grains):
                    if ig==0: C.grain_class=g.__class__
                    g.getMolecules().resize(size=random.randint(5,15))
                    sys.stderr.write(f"Grain #{ig} has {len(g.getMolecules())} molecules\n")
                    for m in g.getMolecules():
                        m.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
                        m.getProperties().getPhysical().getPolarizability().setNeutral(np.array([[1,2,3],[4,5,6],[7,8,9]])*mp.U['Angstrom2 s4 / kg'])
                        m.getAtoms().resize(size=random.randint(10,30))
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
                a,aps=atomCounter,atomCounter/(t1-t0)
                sys.stderr.write(f'{m}: created {a} atoms at {aps:g}/sec.\n')
            # h.closeData()
    def test_02_read(self):
        C=self.__class__
        with mp.HeavyDataHandle(h5path=C.h5path,h5group='test',mode='readonly') as grains:
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
    def test_03_copy(self):
        C=self.__class__
        h1=mp.HeavyDataHandle(h5path=C.h5path,h5group='test')
        h2=h1.cloneHandle()
        self.assertNotEqual(h1.h5path,h2.h5path)
        sys.stderr.write(f'Created temporary file {h2.h5path} for cloneHandle.\n')
        grains=h2.openData(mode='readwrite')
        grains[0].getMolecules()[0].getAtoms()[0].getIdentity().setElement('QQ')
    def test_04_delete(self):
        C=self.__class__
        with mp.HeavyDataHandle(h5path=C.h5path,h5group='test',mode='readwrite') as grains:
            mols=grains[0].getMolecules()
            nmols=len(mols)
            mols.resize(nmols-4)
            self.assertEqual(len(mols),nmols-4)
    def test_05_create_temp(self):
        handle=mp.HeavyDataHandle(schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
        handle.openData(mode='create')
        handle.closeData()
    def test_06_resize(self):
        handle=mp.HeavyDataHandle(schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
        gg=handle.openData(mode='create-memory')
        self.assertEqual(len(gg),0)
        gg.resize(10)
        self.assertEqual(len(gg),10)
        gg.resize(20)
        self.assertEqual(len(gg),20)
    def test_07_dump_inject(self):
        handle=mp.HeavyDataHandle(schemaName='org.mupif.sample.molecule',schemasJson=mp.heavydata.sampleSchemas_json)
        mols=handle.openData(mode='create-memory')
        mols.resize(2)
        mols[0].getIdentity().setMolecularWeight(1*u.g)
        mols[0].getIdentity().setMolecularWeight(1*u.g)
        m0a=mols[0].getAtoms()
        m0a.resize(2)
        m0a.getIdentity()[0].setElement('AA')
        m0a.getIdentity()[1].setElement('BB')

        dmp=mols.to_dump()
        mols_=mp.HeavyDataHandle(schemaName='org.mupif.sample.molecule',schemasJson=mp.heavydata.sampleSchemas_json).openData(mode='create-memory')
        mols_.inject(mols)
        # compare string representation
        self.assertEqual(str(mols.to_dump()),str(mols_.to_dump()))


        # manipulate the dump by hand and assign it
        dmp[0]['identity.molecularWeight']=(1000.,'u') # change mass of mol0 to 1000 u
        dmp[1]['identity.molecularWeight']=(1,u.kg)  # change mass of mol1 to 1 kg
        with mp.HeavyDataHandle(schemaName='org.mupif.sample.molecule',schemasJson=mp.heavydata.sampleSchemas_json,mode='create-memory') as mols2:
            mols2.from_dump(dmp)
            self.assertEqual(mols2[0].getAtoms()[0].getIdentity().getElement(),'AA')
            self.assertEqual(mols2[0].getAtoms()[1].getIdentity().getElement(),'BB')
            # this are the modified parts
            self.assertEqual(mols2[0].getIdentity().getMolecularWeight(),1000*u.Unit('u'))
            self.assertEqual(mols2[1].getIdentity().getMolecularWeight(),1000*u.Unit('g'))

        # inject fragments of data
        mols3=mp.HeavyDataHandle(schemaName='org.mupif.sample.molecule',schemasJson=mp.heavydata.sampleSchemas_json).openData(mode='create-memory')
        mols3.resize(2)
        mols3[0].getAtoms().inject(mols[0].getAtoms())
        self.assertEqual(len(mols3[0].getAtoms()),2)
        self.assertEqual(mols3[0].getAtoms()[0].getIdentity().getElement(),'AA')
        mols3[1].getAtoms().resize(5)
        mols3[1].getAtoms()[4].inject(mols[0].getAtoms()[1])
        self.assertEqual(mols3[1].getAtoms()[4].getIdentity().getElement(),'BB')

        # inject mismatched schema
        self.assertRaises(ValueError,lambda:mols3.inject(mols[0].getAtoms()))

    def test_20_daemon_start(self):
        C=self.__class__
        C.daemon=Pyro5.api.Daemon()
        #C.daemonRun=True
        th=threading.Thread(target=C.daemon.requestLoop) # ,kwargs=dict(loopCondition=lambda: C.daemonRun))
        th.start()
    def test_21_publish(self):
        C=self.__class__
        C.uri=C.daemon.register(handle:=mp.HeavyDataHandle(h5path=C.h5path,h5group='test',mode='readonly'))
        handle.exposeData()
        handle2=mp.HeavyDataHandle(h5path=C.h5path2,h5group='test',schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
        handle2.openData(mode='create') # this actually create the underlying storage
        C.uri2=C.daemon.register(handle2)
        sys.stderr.write(f'Handle URI is {C.uri}, HDF5 URI is {handle.h5uri}\n')
    def test_22_read_local_copy(self):
        C=self.__class__
        try:
            proxy=Pyro5.api.Proxy(C.uri)
            # this MUST be called to get local instance of the handle
            # its constructor will download the HDF5 file, provided exposeData() had been called on the remote
            local=proxy.copyRemote()
            self.assertEqual(local.__class__,mp.heavydata.HeavyDataHandle)
            sys.stderr.write(f'Local handle is a {local.__class__.__name__}\n')
            root=local.openData(mode='readonly')
            # sys.stderr.write(f'Local root has {len(root)} grains, {root.__class__}\n')
            self.assertEqual(C.numGrains,len(root))
            self.assertEqual(root[0].getMolecules()[0].getAtoms()[0].getIdentity().getElement(),'Q')
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_23_read_remote_proxy(self):
        C=self.__class__
        try:
            proxy=Pyro5.api.Proxy(C.uri)
            root=proxy.openData(mode='readonly')
            self.assertEqual(root.__class__,Pyro5.api.Proxy)
            # special methods don't currently work with Pyro5, use __getitem__ instead of [] for now
            self.assertEqual(root[0].getMolecules()[0].getAtoms()[0].getIdentity().getElement(),'Q')
            a0id=root[0].getMolecules()[0].getAtoms()[0].getIdentity()
            self.assertRaises(KeyError,a0id.getAtomicMass) # Q is not a valid element
            # HDF5 is open read-only: "Unable to create group (no write intent on file)"
            # exceptiion type varies (h5py version?)
            self.assertRaises((OSError,ValueError),lambda: a0id.setElement('H')) 
            # self.assertEqual(a0id.getAtomicMass(),1)
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_24_write_remote_proxy(self):
        C=self.__class__
        try:
            t0=time.time()
            atomCounter=0
            # precompiled schemas
            handle=Pyro5.api.Proxy(C.uri2)
            grains=handle.openData(mode='readwrite')
            grains.resize(size=C.numGrains)
            sys.stderr.write(f"There is {len(grains)} grains.\n")
            for ig,g in enumerate(grains):
                if ig==0: C.grain_class=g.__class__
                (molecules:=g.getMolecules()).resize(size=random.randint(5,10))
                sys.stderr.write(f"Grain #{ig} has {len(g.getMolecules())} molecules\n")
                for m in g.getMolecules():
                    m.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
                    (atoms:=m.getAtoms()).resize(size=random.randint(5,10))
                    for a in m.getAtoms():
                        a.getIdentity().setElement(random.choice(['H','N','Cl','Na','Fe']))
                        a.getProperties().getTopology().setPosition((1,2,3)*u.nm)
                        a.getProperties().getTopology().setVelocity((24,5,77)*u.m/u.s)
                        struct=np.array([random.randint(1,20) for i in range(random.randint(5,20))],dtype='l')
                        a.getProperties().getTopology().setStructure(struct)
                        atomCounter+=1
            t1=time.time()
            sys.stderr.write(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).\n')
            # write and read back a single value
            grains[0].getMolecules()[0].getAtoms()[0].getIdentity().setElement('Q')
            self.assertEqual(grains[0].getMolecules()[0].getAtoms()[0].getIdentity().getElement(),'Q')
            handle.closeData()
        except Exception:
            sys.stderr.write(''.join(Pyro5.errors.get_pyro_traceback()))
            self.test_99_daemon_stop()
            raise
    def test_25_daemon_auto_register_unregister(self):
        C=self.__class__
        handle=mp.HeavyDataHandle(h5path=C.h5path,h5group='test',mode='readonly')
        # register the handle with daemon
        # if the parent object is registered, all nested objects should register automatically with the same daemon
        uri0=C.daemon.register(handle)
        grains=handle.openData(mode='readonly')
        mol0=grains.getMolecules(0)
        atom0=mol0.getAtoms(0)
        atom0id=atom0.getIdentity()
        objs=(handle,grains,mol0,atom0,atom0id)
        ids=[o._pyroId for o in objs]
        for o in objs: self.assertEqual(C.daemon,o._pyroDaemon)
        # check object ids are found in the daemon
        for i in ids: C.daemon.proxyFor(i)
        # closing the data should unregister those
        handle.closeData()
        # so check that here; note however that the handle does *not* unregister itself
        for i in ids[1:]: self.assertRaises(Pyro5.errors.DaemonError,lambda i=i: C.daemon.proxyFor(i))

        
    def test_99_daemon_stop(self):
        C=self.__class__
        sys.stderr.write('Stopping daemon\n')
        C.daemon.shutdown()
        #C.daemonRun=False
        #C.daemonThread.join()


