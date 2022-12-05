import unittest
import mupif as mp
import numpy as np
import sys
import os.path
import multiprocessing
import threading
import time
import Pyro5.api
import json
import time, random
import tempfile
import logging
import astropy.units as u

from mupif.heavystruct import sampleSchemas_json

log=logging.getLogger()

#sys.excepthook=Pyro5.errors.excepthook
#Pyro5.config.DETAILED_TRACEBACK=True


class Hdf5HeavyProperty_TestCase(unittest.TestCase):
    def setUp(self): pass
    def test_01_create(self):
        hp=mp.Hdf5HeavyProperty.make(propID=mp.DataID.PID_Concentration,quantity=mp.Quantity(value=np.array([[1,2,3]]),unit='m/s'),valueType=mp.ValueType.Vector)
        self.assertTrue(os.path.getsize(hp.h5path)>0)
        self.assertTrue((hp.value[:]==[[1,2,3]]).all())
        hp.closeData()
        # re-open
        hp2=mp.Hdf5HeavyProperty.loadFromHdf5(h5path=hp.h5path)
        self.assertTrue((hp2.value[:]==[[1,2,3]]).all())
        self.assertEqual(hp2.propID,mp.DataID.PID_Concentration)
        self.assertEqual(hp2.unit,mp.units.Unit('m/s'))


class Hdf5Quantity_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daemon=mp.pyroutil.getDaemon()
    def setUp(self):
        self.n=1000
        self.hq=mp.Hdf5OwningRefQuantity(mode='create',h5loc='/some/path')
        self.hq.allocateDataset(shape=(self.n,3),dtype='f8',unit='m/s') # creates HDF5 file *and* the dataset, all-zero data
        self.hq.value[1]=1
        self.hq.closeData()
    def test_01_assign(self):
        print(self.hq)
        hq=self.hq
        hq.openData(mode='readwrite') # open HDF5 (automatically) and the dataset itself
        hq.value[:]=np.linspace(0,1,self.n)[:,None]
        self.assertAlmostEqual(hq.value[2][0],2*1/(self.n-1))
        hq.value[3]=[1,2,3]
        self.assertEqual(list(hq.value[3]),[1,2,3])

        hq.quantity[4]=(4,5,6)*mp.U['km/h']
        self.assertAlmostEqual(hq.value[4][0],4/3.6) # m/s

        def value00(v): hq.value[0][0]=v
        def quantity00(q): hq.quantity[0][0]=q
        self.assertRaises(ValueError,lambda: value00(10)) # this would assign to a copy, losing the data
        self.assertRaises(ValueError,lambda: quantity00(10*mp.U['m/s'])) # this would assign to a copy, losing the data

    def test_02_readonly(self):
        self.hq.openData(mode='readonly')
        self.assertRaises(OSError,lambda: self.hq.value.__setitem__(2,1))

    def test_03_refQuantity(self):
        print(self.hq)
        self.hq.openData(mode='readwrite')
        # Hdf5RefQuantity shares underlying dataset
        hrq=self.hq.makeRef()
        self.hq.quantity[5]=(1,2,3)*mp.U['m/s']
        self.assertEqual(list(self.hq.quantity[5]),list(hrq.quantity[5]))

    def test_04_hq_1d(self):
        hq=mp.Hdf5OwningRefQuantity(mode='create')
        hq.allocateDataset(shape=(3,),dtype='f4',unit='m/s')
        hq.value[:]=[1,2,3]
        hq.reopenData('readwrite')
        hq.value[1]=44
        self.assertEqual(hq.value[1],44)
        hq.reopenData(mode='readwrite')
        self.assertEqual(hq.value[1],44)
        # broadcasting
        hq.value[:]=33
        hq.reopenData()
        self.assertEqual(hq.value.shape,(3,))
        self.assertTrue((np.array(hq.value)==33).all())
    def test_05_hq_2d(self):
        hq=mp.Hdf5OwningRefQuantity(mode='create')
        hq.allocateDataset(shape=(1,3),dtype='f4',unit='m/s')
        hq.value[0]=[1,2,3]
        hq.reopenData('readwrite')
        hq.value[0]=[44,55,66]
        self.assertEqual(hq.value[0][1],55)
        hq.reopenData(mode='readwrite')
        self.assertEqual(hq.value[0][1],55)
        # broadcasting
        hq.value[:]=33
        hq.reopenData()
        self.assertEqual(hq.value.shape,(1,3))
        self.assertTrue((np.array(hq.value[:])==33).all())


    def test_10_transfer(self):
        C=self.__class__
        # 1. register the Hdf5OwningRefQuantity itself
        uri=C.daemon.register(self.hq)

        # test: exposing open data raises exception
        self.hq.openData(mode='readonly')
        v00=self.hq.value[0][0]
        self.assertRaises(RuntimeError,self.hq.exposeData)
        self.hq.closeData()

        # # 2. expose the data (uses the same daemon); this is now automatic
        # self.hq.exposeData()

        p=Pyro5.api.Proxy(uri)
        # copies backing HDF5 file automatically
        hq2=p.copyRemote()

        hq2.openData(mode='readwrite')
        self.assertEqual(list(hq2.value[1]),[1.,1.,1.])
        # test that backing storage is really different
        self.assertNotEqual(self.hq.h5path,hq2.h5path)
        hq2.value[0]=(100,0,0)
        self.assertNotEqual(v00,hq2.value[0][0])
        self.assertIsNone(hq2.h5uri)
    def test_11_preDumpHook_transfer(self):
        C=self.__class__
        # 1. register the Hdf5OwningRefQuantity itself
        uri=C.daemon.register(self.hq)
        p=Pyro5.api.Proxy(uri)
        self.assertIsNone(self.hq.h5uri)
        # should transfer HDF5 file automatically, via calling exposeData in preDumpHook first
        hq2=p.copyRemote()
        self.assertIsNotNone(self.hq.h5uri)
        self.assertNotEqual(self.hq.h5path,hq2.h5path) # storage should have been copied

    def test_20_makeFromQuantity2d(self):
        q=mp.Quantity(value=np.array([[1,2,3],[4,5,6],[7,8,9]]),unit='m/s')
        hq=mp.Hdf5OwningRefQuantity.makeFromQuantity(q)
        self.assertTrue(os.path.getsize(hq.h5path)>0)
        self.assertEqual(q.value[1][1],hq.value[1][1])
        self.assertEqual(q.value.shape,hq.value.shape)
        self.assertEqual(q.unit,hq.unit)
    def test_21_makeFromQuantity1d(self):
        q=mp.Quantity(value=np.array([1,2,3]),unit='m/s')
        hq=mp.Hdf5OwningRefQuantity.makeFromQuantity(q)
        self.assertTrue(os.path.getsize(hq.h5path)>0)
        self.assertEqual(q.value[1],hq.value[1])
        hq.value[1]=44
        self.assertEqual(hq.value[1],44)
        hq.reopenData(mode='readwrite')
        self.assertEqual(hq.value[1],44)
    def test_23_toQuantity(self):
        self.hq.openData(mode='readonly')
        q=self.hq.toQuantity()
        self.assertEqual(self.hq.unit,q.unit)
        self.assertEqual(self.hq.value.shape,q.shape)
        self.assertEqual(list(self.hq.value[1]),list(q.value[1]))
    def test_24_propertySwapQuantity(self):
        p1=mp.Property(propID=mp.DataID.PID_Concentration,quantity=mp.Quantity(value=np.array([[1,2,3]]),unit='mmol/l'),valueType=mp.ValueType.Vector)
        p2=p1.deepcopy()
        # replace p2's quantity by Hdf5OwningRefQuantity
        p2.quantity=mp.Hdf5OwningRefQuantity.makeFromQuantity(p2.quantity)
        # check stuff
        self.assertTrue(os.path.getsize(p2.quantity.h5path)>0)
        self.assertTrue((p1.value[:]==p2.value[:]).all())
        p2.value[0]=3
        self.assertTrue((p2.value[0]==3).all())

        # re-load p2.quantity from closed HDF5 file
        p2.quantity.closeData()
        q2=mp.Hdf5OwningRefQuantity(h5path=p2.quantity.h5path,h5loc=p2.quantity.h5loc,mode='readonly')
        q2.openData() # open so that we can assign to quantity
        q2a=q2.toQuantity() # onvert to in-memory quantity
        p3=mp.Property(propID=p2.propID,valueType=p2.valueType,quantity=q2.toQuantity())

        self.assertEqual(p1.value.shape,p3.value.shape)
        self.assertTrue((np.array([[3,3,3]])==p3.value[:]).all())
        self.assertEqual(p1.getUnit(),p3.getUnit())

class HeavyStruct_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
        #cls.tmp='/tmp/'
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
                mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='create',schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json),
                mp.HeavyStruct(mode='create-memory',schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json)
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
                    g.getProperties().setSymmetry('periodic')
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
        with mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readonly') as grains:
            t0=time.time()
            atomCounter=0
            for g in grains:
                self.assertEqual(C.grain_class.__module__,g.__class__.__module__)
                self.assertEqual(C.grain_class.__name__,g.__class__.__name__)
                self.assertEqual(g.getProperties().getSymmetry(),'periodic')
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
    def test_03_clone_handle(self):
        C=self.__class__
        h1=mp.HeavyStruct(h5path=C.h5path,h5group='test')
        h2=h1.cloneHandle()
        self.assertNotEqual(h1.h5path,h2.h5path)
        sys.stderr.write(f'Created temporary file {h2.h5path} for cloneHandle.\n')
        grains=h2.openData(mode='readwrite')
        grains[0].getMolecules()[0].getAtoms()[0].getIdentity().setElement('QQ')
    def test_04_copy_readwrite(self):
        C=self.__class__
        hs=mp.HeavyStruct(h5path=C.h5path,h5group='test')
        hs.openData(mode='copy-readwrite')
        # should copy to temporary
        self.assertNotEqual(C.h5path,hs.h5path)
        hs.closeData()
        self.assertEqual(os.path.getsize(C.h5path),os.path.getsize(hs.h5path))
    def test_05_delete(self):
        C=self.__class__
        with mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readwrite') as grains:
            mols=grains[0].getMolecules()
            nmols=len(mols)
            mols.resize(nmols-4)
            self.assertEqual(len(mols),nmols-4)
    def test_06_create_temp(self):
        handle=mp.HeavyStruct(schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json)
        handle.openData(mode='create')
        handle.closeData()
    def test_07_resize(self):
        handle=mp.HeavyStruct(schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json)
        gg=handle.openData(mode='create-memory')
        self.assertEqual(len(gg),0)
        gg.resize(10)
        self.assertEqual(len(gg),10)
        gg.resize(20)
        self.assertEqual(len(gg),20)
    def test_08_dump_inject(self):
        handle=mp.HeavyStruct(schemaName='org.mupif.sample.molecule',schemasJson=sampleSchemas_json)
        mols=handle.openData(mode='create-memory')
        mols.resize(2)
        mols[0].getIdentity().setMolecularWeight(1*u.g)
        mols[0].getIdentity().setMolecularWeight(1*u.g)
        m0a=mols[0].getAtoms()
        m0a.resize(2)
        m0a.getIdentity()[0].setElement('AA')
        m0a.getIdentity()[1].setElement('BB')

        dmp=mols.to_dump()
        mols_=mp.HeavyStruct(schemaName='org.mupif.sample.molecule',schemasJson=sampleSchemas_json).openData(mode='create-memory')
        mols_.inject(mols)
        # compare string representation
        self.assertEqual(str(mols.to_dump()),str(mols_.to_dump()))


        # manipulate the dump by hand and assign it
        dmp[0]['identity.molecularWeight']=(1000.,'u') # change mass of mol0 to 1000 u
        dmp[1]['identity.molecularWeight']=(1,u.kg)  # change mass of mol1 to 1 kg
        with mp.HeavyStruct(schemaName='org.mupif.sample.molecule',schemasJson=sampleSchemas_json,mode='create-memory') as mols2:
            mols2.from_dump(dmp)
            self.assertEqual(mols2[0].getAtoms()[0].getIdentity().getElement(),'AA')
            self.assertEqual(mols2[0].getAtoms()[1].getIdentity().getElement(),'BB')
            # this are the modified parts
            self.assertEqual(mols2[0].getIdentity().getMolecularWeight(),1000*u.Unit('u'))
            self.assertEqual(mols2[1].getIdentity().getMolecularWeight(),1000*u.Unit('g'))

        # inject fragments of data
        mols3=mp.HeavyStruct(schemaName='org.mupif.sample.molecule',schemasJson=sampleSchemas_json).openData(mode='create-memory')
        mols3.resize(2)
        mols3[0].getAtoms().inject(mols[0].getAtoms())
        self.assertEqual(len(mols3[0].getAtoms()),2)
        self.assertEqual(mols3[0].getAtoms()[0].getIdentity().getElement(),'AA')
        mols3[1].getAtoms().resize(5)
        mols3[1].getAtoms()[4].inject(mols[0].getAtoms()[1])
        self.assertEqual(mols3[1].getAtoms()[4].getIdentity().getElement(),'BB')

        # inject mismatched schema
        self.assertRaises(ValueError,lambda:mols3.inject(mols[0].getAtoms()))
    def test_09_schema_storage(self):
        C=self.__class__
        with (hs:=mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readonly')) as grains:
            self.assertEqual(hs.getSchemaName(),'org.mupif.sample.grain')
            self.assertEqual(hs.getSchemasJson(),sampleSchemas_json)
        # data closed, should not work
        self.assertRaises(RuntimeError,lambda: hs.getSchemaName())
    def test_10_move_storage(self):
        C=self.__class__
        p0,p1=C.tmp+'/grain-before-move.h5',C.tmp+'/grain-after-move.h5'
        with (hs:=mp.HeavyStruct(h5path=p0,mode='create',schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json)) as grains:
            grains.resize(size=100)
            self.assertRaises(RuntimeError,lambda: hs.moveStorage(p1))
        hs.moveStorage(p1)
        self.assertEqual(hs.h5path,p1)
        self.assertFalse(os.path.exists(p0))
        self.assertTrue(os.path.exists(p1))
    def test_20_daemon_start(self):
        C=self.__class__
        C.daemon=mp.pyroutil.getDaemon()
    def test_21_publish(self):
        C=self.__class__
        C.uri=C.daemon.register(handle:=mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readonly'))
        handle.exposeData()
        handle2=mp.HeavyStruct(h5path=C.h5path2,h5group='test',schemaName='org.mupif.sample.grain',schemasJson=sampleSchemas_json)
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
            self.assertEqual(local.__class__,mp.heavystruct.HeavyStruct)
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
        handle=mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readonly')
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
    def test_30_deepcopy(self):
        C=self.__class__
        hsLoc=mp.HeavyStruct(h5path=C.h5path,h5group='test',mode='readonly')
        hsRem=Pyro5.api.Proxy(C.daemon.register(hsLoc))
        hsLoc2=hsLoc.deepcopy() # copies HDF5 via file copy
        hsRem2=hsRem.deepcopy() # copies HDF5 via exposing data throught the daemon and downloading them in the local constructor
        self.assertTrue(isinstance(hsRem,Pyro5.api.Proxy))
        self.assertTrue(isinstance(hsRem2,mp.HeavyStruct))
        self.assertNotEqual(hsLoc.h5path,hsLoc2.h5path)
        hsRemAttrs=hsRem.to_dict(clss=hsLoc.__class__)
        self.assertNotEqual(hsRemAttrs['h5path'],hsRem2.h5path)

    def test_30_delimiter(self):
        schema='''
            [
              {
                "_schema": {
                  "name": "test",
                  "version": "1.0"
                },
                "_datasetName": "test",
                "str10":{ "dtype":"a10" },
                "str":{ "dtype":"a" },
                "lst100":{ "dtype":"a100", "delim":"|" },
                "lst": { "dtype":"a", "delim":"|||" }
              }
            ]
        '''
        with mp.HeavyStruct(mode='create-memory',schemaName='test',schemasJson=schema) as tests:
            tests.resize(1)
            t0=tests[0]
            self.assertRaises(TypeError,lambda: t0.setStr10(10*'aa')) # content too long
            t0.setStr10('str10')
            t0.setStr('dynamic-str')
            self.assertRaises(TypeError,lambda: t0.setLst100(100*['hi']))
            self.assertRaises(BaseException,lambda: t0.setLst100(['this contains the | delimiter and should fail']))
            t0.setLst100(10*['lst100'])
            print(t0.getLst100())
            print(10*['lst100'])
            self.assertRaises(BaseException,lambda: t0.setLst(['contains the ||| delimiter and should fail']))
            self.assertRaises(TypeError,lambda: t0.setLst('this is a string, not a list'))
            t0.setLst(1000*['dynamic-string-list'])
            def modify_inplace(t): t0.getLst()[1]='foo'
            self.assertRaises(TypeError, modify_inplace)
            self.assertEqual(t0.getStr10(),'str10')
            self.assertEqual(t0.getStr(),'dynamic-str')
            self.assertEqual(t0.getLst100(),tuple(10*['lst100']))
            self.assertEqual(t0.getLst(),tuple(1000*['dynamic-string-list']))

    def test_31_json(self):
        schema='''
            [
              {
                "_schema": { "name": "test" },
                "json":{ "dtype":"json" }
              }
            ]
        '''
        with mp.HeavyStruct(mode='create-memory',schemaName='test',schemasJson=schema) as tests:
            tests.resize(1)
            t0=tests[0]
            data=['abc',dict(foo='bar',baz='baz',d={'123':456})]
            t0.setJson(data)
            self.assertEqual(t0.getJson(),data)

    def test_31_namingConvention(self):
        schema='''
            [{
                "_schema": { "name": "test", "naming":"property" },
                "str10":{ "dtype":"a10" }
            }]
        '''
        with mp.HeavyStruct(mode='create-memory',schemaName='test',schemasJson=schema) as tests:
            tests.resize(1)
            t0=tests[0]
            t0.str10='sdfd'
            self.assertRaises(TypeError,lambda: setattr(t0,'str10',10*'aa')) # content too long
            self.assertEqual(t0.str10,'sdfd')

    def test_32_indexed(self):
        schema='''
            [
              {
                "_schema": { "name": "testA", "naming":"property" },
                "refB_raw": { "dtype":"int64" },
                "refBB_raw": { "dtype":"int64", "shape":"variable" },
                "refB":{ "indexed":"refB_raw", "path":"testB"  },
                "refBB":{ "indexed":"refBB_raw", "path":"testB" }
              },
              {
                "_schema": { "name": "testB", "naming":"property" },
                "name": { "dtype": "a20" }
              }
            ]
        '''
        with mp.HeavyStruct(mode='create-memory',schemaName='testA',schemasJson=schema) as a:
            a.resize(1)
            b=a.refB
            b.resize(3) # this is the entire testB dataset, since "a" is not indexed
            self.assertEqual(len(b),3)
            b[0].name,b[1].name,b[2].name='zeroth','first','second'
            a0=a[0]
            a0.refB_raw=1
            self.assertEqual(a0.refB_raw,1)
            b1=a0.refB
            log.error(b1)
            self.assertEqual(b1.name,'first')
            a0.refBB_raw=np.array([0,1,2,1,0])
            bb=a0.refBB
            self.assertEqual(len(bb),len(a0.refBB_raw))
            for b,name in zip(bb,['zeroth','first','second','first','zeroth']): self.assertEqual(b.name,name)
            self.assertEqual(len(a.refBB),3) # same dataset as a.refB


    def test_40_mupifObject(self):
        schema='''
            [
              {
                "_schema": { "name": "test" },
                "field": { "dtype":"i", "mupifType":"mupif.Field" },
                "fields": { "dtype":"i", "shape":"variable", "mupifType":"mupif.Field" }
              }
            ]
        '''
        box=mp.demo.make_meshio_box_hexa(dim=(1,2,3),sz=.1)
        mesh=mp.Mesh.makeFromMeshioMesh(box)
        f1=mp.Field(mesh=mesh,fieldID=mp.DataID.FID_Displacement,valueType=mp.ValueType.Scalar,time=13*mp.Q.s,quantity=[(.001*i,) for i in range(mesh.getNumberOfVertices())]*mp.U.m,fieldType=mp.FieldType.FT_vertexBased)
        f2=mp.Field(mesh=mesh,fieldID=mp.DataID.FID_Strain,valueType=mp.ValueType.Vector,time=128*mp.Q.s,quantity=[(.1*i,.2*i,.3*i) for i in range(mesh.getNumberOfVertices())]*mp.U['kg/(m*s**2)'],fieldType=mp.FieldType.FT_vertexBased)

        with mp.HeavyStruct(mode='create-memory',schemaName='test',schemasJson=schema) as tests:
            tests.resize(1)
            t0=tests[0]
            t0.setField(f2)
            f2a=t0.getField()
            self.assertTrue(isinstance(f2a,mp.Field))
            t0.setFields([f1,f2])
            t0.appendFields(f1)
            t0.appendFields(f2)
            self.assertEqual(len(t0.getFields()),4)
            self.assertEqual(len(t0.ctx.dataset.parent['mupif-obj/fields']),5)
            # check that mesh object is shared
            self.assertEqual(len(t0.ctx.dataset.parent['mupif-obj/meshes']),1)




class HeavyMesh_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.box=mp.demo.make_meshio_box_hexa(dim=(1,2,3),sz=.1)
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
    @classmethod
    def tearDownClass(cls):
        try: cls.tmpdir.cleanup()
        except: pass # this would fail under Windows
    def test_saveload(self):
        cls=self.__class__
        h5path=f'{cls.tmp}/01-mesh.h5'
        xdmfPath=f'{cls.tmp}/01-mesh.xdmf'
        evalAt=(.1,.1,.1)
        with mp.HeavyUnstructuredMesh(h5path=h5path,mode='overwrite') as mesh:
            mesh.fromMeshioMesh(cls.box)
            fieldP=mesh.makeHeavyField(unit='Pa',fieldID=mp.DataID.FID_Pressure,fieldType=mp.FieldType.FT_cellBased,valueType=mp.ValueType.Scalar)
            fieldUVW=mesh.makeHeavyField(unit='m/s',fieldID=mp.DataID.FID_Velocity,fieldType=mp.FieldType.FT_cellBased,valueType=mp.ValueType.Vector)
            fieldP.value[:]=np.linspace(0,1,mesh.getNumberOfCells())
            # mesh.writeXDMF(xdmfPath,fields=[fieldP,fieldUVW]) # this is actually not necessary
            val0=fieldP.evaluate(evalAt)
        # load mesh and fields from HDF5, also opens the storage
        mesh,fields=mp.HeavyUnstructuredMesh.load(h5path)
        val1=fields[0].evaluate((.1,.1,.1))
        self.assertEqual(val0,val1)
        mesh.closeData()

