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
        pf=mp.PyroFile(C.A,'rb')
        a1=C.tmp+'/A01'
        mp.pyroutil.downloadPyroFile(a1,pf)
        self.assertEqual(C.Adata,open(a1,'rb').read())
    def test_pyroFile_proxied(self):
        'Fetch PyroFile content through Pyro'
        C=self.__class__
        pf=mp.PyroFile(C.A,'rb')
        a2=C.tmp+'/A02'
        uri=C.daemon.register(pf)
        pfp=Pyro5.api.Proxy(uri)
        mp.pyroutil.downloadPyroFile(a2,pfp)
        self.assertEqual(C.Adata,open(a2,'rb').read())
    def test_pyroFile_already_proxied(self):
        'Passing PyroFile through Pyro (autoproxy)'
        C=self.__class__
        pf=mp.PyroFile(C.A,'rb')
        uri=C.daemon.register(pf)
        # serialization/deserialization rountrip yields Proxy object (if the PyroFile is exposed)
        ser=Pyro5.serializers.serializers['serpent']
        r=ser.loads(ser.dumps(pf))
        self.assertEqual(type(r),Pyro5.api.Proxy)
        self.assertEqual(str(r._pyroUri),str(uri))
    def test_pyroFile_copyTo(self):
        'Copy file between proxies'
        C=self.__class__
        a3=C.tmp+'/A03'
        a4=C.tmp+'/A04'
        a5=C.tmp+'/A05'
        a6=C.tmp+'/A06'
        src=C.daemon.register(mp.PyroFile(C.A,'rb'))
        dst=C.daemon.register(mp.PyroFile(a3,'wb'))
        dst6=C.daemon.register(mp.PyroFile(a6,'wb'))
        srcP,dstP,dstP6=Pyro5.api.Proxy(src),Pyro5.api.Proxy(dst),Pyro5.api.Proxy(dst6)
        mp.PyroFile.copyTo(srcP,dstP,compress=True) # use existing PyroFile (via Proxy); with compression
        mp.PyroFile.copyTo(srcP,a4,compress=False) # creates temporary ProxyFile (local); test without compression
        mp.PyroFile.copyTo(C.A,a5) # should do a direct copy (without PyroFile)
        mp.PyroFile.copyTo(C.A,dstP6) # copy local to remote PyroFile ("upload")
        self.assertEqual(C.Adata,open(a3,'rb').read())
        self.assertEqual(C.Adata,open(a4,'rb').read())
        self.assertEqual(C.Adata,open(a5,'rb').read())
        self.assertEqual(C.Adata,open(a6,'rb').read())



