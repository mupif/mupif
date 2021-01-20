import sys
sys.path.append('../..')

import unittest
from mupif import *
import math
import mupif.physics.physicalquantities as PQ
import os



class EnsightReader2_TestCase(unittest.TestCase):
    # Testing getIntegrationPoints
    def test_ReadEnsightGeo(self):
        parts=[1, 2]
        partRec=[]
        THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
        my_file = os.path.join(THIS_FOLDER, 'testEnsightReader.geo')
        mesh = ensightreader2.readEnsightGeo(my_file, parts, partRec)
#        mesh = ensightreader2.readEnsightGeo('MMPTestCase_v1.geo', parts, partRec)
        timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])
        temperatureUnits = PQ.PhysicalUnit('K',   1.,    [0,0,0,0,1,0,0,0,0])
#        f = ensightreader2.readEnsightField('fld_TEMPERATURE.escl', parts, partRec, 1, FieldID.FID_Temperature, mesh, temperatureUnits, 0)
        self.assertTrue(1==1)


if __name__ == '__main__': unittest.main()


