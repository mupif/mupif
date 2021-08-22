import sys
sys.path.extend(['..', '../..'])
import mupif as mp


if __name__ == '__main__':
    lut = mp.MemoryLookupTable()
    lut.setData([
        [0., 1., 2., 3.],
        [1., 2., 3., 4.],
        [2., 3., 4., 5.]
    ])

    print(lut.evaluate([3., 4., 5.]))
    print(lut.evaluate([0., 1., 2.]))
    print(lut.evaluate([1., 2., 3.]))
    print(lut.evaluate([2., 3., 4.]))
