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

class PyroFile_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daemon=Pyro5.api.Daemon()
        th=threading.Thread(target=cls.daemon.requestLoop)
        th.start()
        cls.tmpdir=tempfile.TemporaryDirectory()
        cls.tmp=cls.tmpdir.name
        cls.A=cls.tmp+'/A'
        cls.Adata=bytes(''.join(random.choices(string.ascii_letters+string.digits,k=1000)),encoding='utf-8')
        f=open(cls.A,'wb')
        f.write(cls.Adata)
        f.close()
    @classmethod
    def tearDownClass(cls):
        cls.daemon.shutdown()
        try: cls.tmpdir.cleanup()
        except: pass # this is for windows
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



class MupifObject_TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daemon=Pyro5.api.Daemon()
        th=threading.Thread(target=cls.daemon.requestLoop)
        th.start()
    @classmethod
    def tearDownClass(cls):
        cls.daemon.shutdown()
        try: cls.tmpdir.cleanup()
        except: pass # this is for windows
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

