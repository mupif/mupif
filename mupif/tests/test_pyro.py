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
import string
import astropy.units as u
import logging
import os.path
import appdirs

srcNsFile=os.path.dirname(os.path.abspath(mp.__file__))+'/MUPIF_NS'
cfgNsFile=appdirs.user_config_dir()+'/MUPIF_NS'

class PyroNS(unittest.TestCase):
    @unittest.skipIf(os.path.exists(srcNsFile) or os.path.exists(cfgNsFile),f'Pre-existing {srcNsFile} or {cfgNsFile}.')
    def test_mupifns_precedence(self):
        # first create all MUPIF_NS and then take away starting from the highest precedence
        # if user-config MUPIF_NS exists or module-level MUPIF_NS exists, skip the test
        # as we don't want to overwrite someone's config.
        # The test will not be skipped in the CI as there is no pre-existing config there.

        # 1. args passed to locateNameserver
        pass
        # 2. env var
        os.environ['MUPIF_NS']='2.2.2.2:2222'
        # 3. MUPIF_NS in mupif module directory
        assert not os.path.exists(srcNsFile)
        srcNs=('3.3.3.3',3333)
        open(srcNsFile,'w').write(f'3.3.3.3:3333')
        # 4. XDG config directory
        assert not os.path.exists(cfgNsFile)
        open(cfgNsFile,'w').write('4.4.4.4:4444')
        # 5. fallback values

        # 1. args
        self.assertEqual(mp.pyroutil.locateNameserver('1.1.1.1',1111),('1.1.1.1',1111))
        # 2. env var
        self.assertEqual(mp.pyroutil.locateNameserver(),('2.2.2.2',2222))
        del os.environ['MUPIF_NS']
        # 3. module dir
        self.assertEqual(mp.pyroutil.locateNameserver(),srcNs)
        os.remove(srcNsFile)
        # 4. user config
        self.assertEqual(mp.pyroutil.locateNameserver(),('4.4.4.4',4444))
        os.remove(cfgNsFile)
        # 5. fallback values
        # broadcast lookup for client
        self.assertEqual(mp.pyroutil.locateNameserver(),(None,0))
        # bind localhost for server
        self.assertEqual(mp.pyroutil.locateNameserver(server=True),('127.0.0.1',9090))



class PyroFile_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daemon=mp.pyroutil.getDaemon()
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
        cls.A=cls.tmp+'/A.bin'
        cls.Adata=os.urandom(1000)
        f=open(cls.A,'wb')
        f.write(cls.Adata)
        f.close()
    def test_pyroFile_local(self):
        'Fetch PyroFile content directly'
        C=self.__class__
        pf=mp.PyroFile(filename=C.A,mode='rb')
        a1=C.tmp+'/A01'
        mp.PyroFile.copy(pf,a1)
        self.assertEqual(C.Adata,open(a1,'rb').read())
    def test_pyroFile_proxied(self):
        'Fetch PyroFile content through Pyro'
        C=self.__class__
        pf=mp.PyroFile(filename=C.A,mode='rb')
        a2=C.tmp+'/A02'
        uri=C.daemon.register(pf)
        pfp=Pyro5.api.Proxy(uri)
        mp.PyroFile.copy(pfp,a2)
        self.assertEqual(C.Adata,open(a2,'rb').read())
    def test_pyroFile_already_proxied(self):
        'Passing PyroFile through Pyro (autoproxy)'
        C=self.__class__
        pf=mp.PyroFile(filename=C.A,mode='rb')
        uri=C.daemon.register(pf)
        # serialization/deserialization rountrip yields Proxy object (if the PyroFile is exposed)
        ser=Pyro5.serializers.serializers['serpent']
        r=ser.loads(ser.dumps(pf))
        self.assertEqual(type(r),Pyro5.api.Proxy)
        self.assertEqual(str(r._pyroUri),str(uri))
    def test_pyroFile_copy(self):
        'Copy file between proxies'
        C=self.__class__
        a3=C.tmp+'/A03'
        a4=C.tmp+'/A04'
        a5=C.tmp+'/A05'
        a6=C.tmp+'/A06'
        src=C.daemon.register(mp.PyroFile(filename=C.A,mode='rb'))
        dst=C.daemon.register(mp.PyroFile(filename=a3,mode='wb'))
        dst6=C.daemon.register(mp.PyroFile(filename=a6,mode='wb'))
        srcP,dstP,dstP6=Pyro5.api.Proxy(src),Pyro5.api.Proxy(dst),Pyro5.api.Proxy(dst6)
        mp.PyroFile.copy(srcP,dstP,compress=True) # use existing PyroFile (via Proxy); with compression
        mp.PyroFile.copy(srcP,a4,compress=False) # creates temporary ProxyFile (local); test without compression
        mp.PyroFile.copy(C.A,a5) # should do a direct copy (without PyroFile)
        mp.PyroFile.copy(C.A,dstP6) # copy local to remote PyroFile ("upload")
        self.assertEqual(C.Adata,open(a3,'rb').read())
        self.assertEqual(C.Adata,open(a4,'rb').read())
        self.assertEqual(C.Adata,open(a5,'rb').read())
        self.assertEqual(C.Adata,open(a6,'rb').read())
    def test_pyroFile_copy_chunks(self):
        C=self.__class__
        aa=[f'{C.tmp}/A1{i}' for i in range(4)]
        src=mp.PyroFile(filename=C.A,mode='rb')
        src.setBufSize(100)
        srcUri=C.daemon.register(src)
        ddst=[C.daemon.register(mp.PyroFile(filename=a,mode='wb')) for a in aa]
        ddstP=[Pyro5.api.Proxy(dst) for dst in ddst]
        # use tiny buffer on the reading side to force chunking
        srcP=Pyro5.api.Proxy(srcUri)
        mp.PyroFile.copy(src,aa[0],compress=True)
        mp.PyroFile.copy(src,aa[1],compress=False)
        mp.PyroFile.copy(srcP,ddstP[2],compress=True)
        mp.PyroFile.copy(srcP,ddstP[3],compress=False)
        for i in range(4):
            self.assertEqual(C.Adata,open(aa[i],'rb').read())
    def test_pyroFile_basename(self):
        'PyroFile.getBasename()'
        C=self.__class__
        pf=mp.PyroFile(filename=C.A,mode='rb')
        uri=C.daemon.register(pf)
        pfp=Pyro5.api.Proxy(uri)
        import os.path
        self.assertEqual(pf.getBasename(),os.path.basename(C.A))
        self.assertEqual(pfp.getBasename(),os.path.basename(C.A))
    def test_pyrofile_dataid_enum(self):
        'PyroFile.getDataID()'
        # check that DataID is correctly (de)serialized as mp.DataID (registered in __init__.py, along with enum.Enum)
        C=self.__class__
        pf=mp.PyroFile(filename=C.A,mode='rb',dataID=mp.DataID.FID_Displacement)
        uri=C.daemon.register(pf)
        pfp=Pyro5.api.Proxy(uri)
        self.assertEqual(pfp.getDataID(),mp.DataID.FID_Displacement)
        self.assertEqual(type(pfp.getDataID()),mp.DataID)




class MupifObject_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daemon=mp.pyroutil.getDaemon() # Pyro5.api.Daemon()
    def test_isInstance(self):
        'Remote/local call of MupifObjectBase.isInstance'
        C=self.__class__
        obj=mp.MupifObjectBase(metadata={'foo':'bar'})
        uri=C.daemon.register(obj)
        pro=Pyro5.api.Proxy(uri)
        self.assertFalse(pro.isInstance(str))
        self.assertTrue(pro.isInstance(mp.MupifObjectBase))
        self.assertTrue(pro.isInstance((mp.MupifObjectBase,int)))
        self.assertFalse(obj.isInstance(str))
        self.assertTrue(obj.isInstance(mp.MupifObjectBase))
        self.assertTrue(obj.isInstance((mp.MupifObjectBase,int)))
