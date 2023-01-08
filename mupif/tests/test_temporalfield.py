import unittest
import pytest
import tempfile
from mupif import *
import mupif as mp
import math
import os
import os.path
import numpy as np
import astropy.units as au


def mkVertex(number, label, coords): return vertex.Vertex(number=number, label=label, coords=coords)


class TemporalField_TestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self.tmpdir.name
        # self.tmp, self.tmpdir = '/tmp/aa', None

        self.mesh = mesh.UnstructuredMesh()
        self.mesh.setup([
            mkVertex(0, 0, (0., 0., 0.)),
            mkVertex(1, 1, (2., 0., 0.)),
            mkVertex(2, 2, (0., 5., 0.)),
            mkVertex(3, 3, (4., 2., 0.)),
            mkVertex(4, 4, (5., 4., 0.)),
            mkVertex(5, 5, (.5, 5.5, 0)),
        ], [
            cell.Triangle_2d_lin(mesh=self.mesh, number=1, label=1, vertices=(0, 1, 2)),
            cell.Triangle_2d_lin(mesh=self.mesh, number=2, label=2, vertices=(1, 2, 3)),
            cell.Quad_2d_lin(mesh=self.mesh, number=3, label=3, vertices=(2, 3, 4, 5))
        ])
        self.displ = []
        self.accel = []
        self.times = (0, 1, 2, 5, 10, 20, 50)
        for t in self.times:
            self.displ.append(
                field.Field(
                    mesh=self.mesh, fieldID=DataID.FID_Displacement, valueType=ValueType.Scalar, time=t*au.s,
                    quantity=[(100*t+0,), (100*t+1,), (100*t+2,), (100*t+3,), (100*t+4,), (100*t+5,)]*au.m,
                    fieldType=FieldType.FT_vertexBased
                )
            )
            self.accel.append(
                field.Field(
                    mesh=self.mesh, fieldID=DataID.FID_Strain, valueType=ValueType.Vector, time=t*au.s,
                    quantity=[(100*t+2*i, 100*t+2*i+1) for i in range(6)]*au.Unit('kg/(m*s**2)'),
                    fieldType=FieldType.FT_vertexBased
                )
            )

    def tearDown(self):
        if self.tmpdir:
            self.tmpdir.cleanup()

    def test_01_construct(self):
        def _do(tf, dir=None):
            self.assertEqual(tf.timeList(), [])
            for i, f in enumerate(self.displ):
                tf.addField(f, userMetadata={'foo': 'bar', 'ordinal': i})
            self.assertEqual(tf.timeList(), [t*au.s for t in self.times])
            self.assertRaises(ValueError, lambda: tf.addField(self.displ[0], userMetadata={}))
            if dir:
                # correct mesh deduplication
                self.assertEqual(len(os.listdir(dir+'/mesh')), 1)
                # correct number of fields
                self.assertEqual(len(os.listdir(dir+'/field')), len(self.times))
            # correct metadata
            self.assertEqual(tf.timeMetadata(1*au.s)['user'], {'foo': 'bar', 'ordinal': 1})
            # correct instances
            f = tf.getField(time=1*au.s)
            m = f.getMesh()
            # print(f'MESH {m.__class__.__module__}.{m.__class__.__name__}')
            # print('IS',m,isinstance(m,mp.HeavyUnstructuredMesh))
            self.assertTrue(isinstance(f.getMesh(), mp.HeavyUnstructuredMesh))
            # print('Q',f.quantity)
            if dir:
                self.assertTrue(isinstance(f.quantity, mp.Hdf5OwningRefQuantity))
            else:
                self.assertTrue(isinstance(f.quantity, mp.Hdf5RefQuantity))
        tf1 = mp.DirTemporalField(dir=self.tmp)
        _do(tf1)
        if 1:
            tf2 = mp.SingleFileTemporalField(mode='overwrite', h5path=self.tmp+'/single-01.h5')
            tf2.openData(mode=None)
            _do(tf2)
            tf2.closeData()

    def test_02_eval(self):
        def _do(tf, dir=None):
            for f in self.displ:
                tf.addField(f, userMetadata={})
            pos = (.1, .1, 0)
            # evaluation correctly finds field at given time point
            self.assertEqual(tf.evaluate(time=1*au.s, positions=pos), self.displ[1].evaluate(positions=pos))
            # field was cached by evaluate for future use
            self.assertEqual(tf.getCachedTimes(), set([1*au.s]))
            # undefined time point, no evaluation done
            self.assertRaises(ValueError, lambda: tf.evaluate(time=-1*au.s, positions=pos))
        _do(mp.DirTemporalField(dir=self.tmp))
        tf2 = mp.SingleFileTemporalField(mode='overwrite', h5path=self.tmp+'/single-02.h5')
        tf2.openStorage()
        _do(tf2)
        tf2.closeData()

    def test_03_singlefile(self):
        # save fields into new SingleFileTemporalField
        h5path = self.tmp+'/single-03.h5'
        with mp.SingleFileTemporalField(mode='overwrite', h5path=h5path) as tf:
            for f in self.displ:
                tf.addField(f, userMetadata={})
        self.assertTrue(os.path.exists(h5path))
        # open the field again, see that we can access stored fields
        with mp.SingleFileTemporalField(mode='readonly', h5path=h5path) as tf:
            pos = (.1, .1, 0)
            self.assertEqual(tf.evaluate(time=1*au.s, positions=pos), self.displ[1].evaluate(positions=pos))
            self.assertEqual(set(tf.timeList()), set([f.getTime() for f in self.displ]))
            tf.writeXdmf(timeUnit=au.Unit('ms'))


if __name__ == '__main__':
    pytest.main([__file__])
