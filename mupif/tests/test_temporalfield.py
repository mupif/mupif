import unittest
import pytest
import tempfile
from mupif import *
import mupif as mp
import math, os
import numpy as np
import astropy.units as au

def mkVertex(number,label,coords): return vertex.Vertex(number=number,label=label,coords=coords)

class TemporalField_TestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir=tempfile.TemporaryDirectory()
        self.tmp=self.tmpdir.name
        #self.tmp,self.tmpdir='/tmp/aa',None


        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup([
            mkVertex(0,0,(0.,0.,0.)),
            mkVertex(1,1,(2.,0.,0.)),
            mkVertex(2,2,(0.,5.,0.)),
            mkVertex(3,3,(4.,2.,0.)),
            mkVertex(4,4,(5.,4.,0.)),
            mkVertex(5,5,(.5,5.5,0)),
        ],[
            cell.Triangle_2d_lin(mesh=self.mesh,number=1,label=1,vertices=(0,1,2)),
            cell.Triangle_2d_lin(mesh=self.mesh,number=2,label=2,vertices=(1,2,3)),
            cell.Quad_2d_lin(mesh=self.mesh,number=3,label=3,vertices=(2,3,4,5))
        ])
        self.displ=[]
        self.accel=[]
        self.times=(0,1,2,5,10,20,50)
        for t in self.times:
            self.displ.append(
                field.Field(mesh=self.mesh,fieldID=DataID.FID_Displacement,valueType=ValueType.Scalar,time=t*au.s,
                    quantity=[(100*t+0,),(100*t+1,),(100*t+2,),(100*t+3,),(100*t+4,),(100*t+5,)]*au.m,
                    fieldType=FieldType.FT_vertexBased
                )
            )
            self.accel.append(
                field.Field(mesh=self.mesh,fieldID=DataID.FID_Strain,valueType=ValueType.Vector,time=t*au.s,
                    quantity=[(100*t+2*i,100*t+2*i+1) for i in range(6)]*au.Unit('kg/(m*s**2)'),
                    fieldType=FieldType.FT_vertexBased
                )
            )
    def tearDown(self):
        if self.tmpdir: self.tmpdir.cleanup()

    def test_01_construct(self):
        tf=mp.DirTemporalField(dir=self.tmp)
        self.assertEqual(tf.timeList(),[])
        for i,f in enumerate(self.displ):
            tf.addField(f,userMetadata={'foo':'bar','ordinal':i})
        self.assertEqual(tf.timeList(),[t*au.s for t in self.times])
        self.assertRaises(ValueError,lambda:tf.addField(self.displ[0],userMetadata={}))
        # correct mesh deduplication
        self.assertEqual(len(os.listdir(self.tmp+'/mesh')),1)
        # correct number of fields
        self.assertEqual(len(os.listdir(self.tmp+'/field')),len(self.times))
        # correct metadata
        self.assertEqual(tf.timeMetadata(1*au.s)['user'],{'foo':'bar','ordinal':1})
        # correct instances
        f=tf.getField(time=1*au.s)
        self.assertTrue(isinstance(f.getMesh(),mp.HeavyUnstructuredMesh))
        self.assertTrue(isinstance(f.quantity,mp.Hdf5OwningRefQuantity))

    def test_02_eval(self):
        tf=mp.DirTemporalField(dir=self.tmp)
        for f in self.displ: tf.addField(f,userMetadata={})
        pos=(.1,.1,0)
        # evaluation correctly finds field at given time point
        self.assertEqual(tf.evaluate(time=1*au.s,positions=pos),self.displ[1].evaluate(positions=pos))
        # field was cached by evaluate for future use
        self.assertEqual(tf.getCachedTimes(),set([1*au.s]))
        # undefined time point, no evaluation done
        self.assertRaises(ValueError,lambda:tf.evaluate(time=-1*au.s,positions=pos))

if __name__=='__main__':
    pytest.main([__file__])

