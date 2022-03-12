import sys
sys.path.extend(['..', '../..'])
import mupif as mp
from mupif import U


if __name__ == '__main__':
    lut = mp.MemoryLookupTable(data=[
        [0., 1., 2., 3.],
        [1., 2., 3., 4.],
        [2., 3., 4., 5.]
    ], units=[U.s, U.m, U.mm, U.kg])

    print(lut.evaluate([3.*U.m, 4.*U.mm, 5.*U.kg]))  # produces 2. s
    print(lut.evaluate([0.*U.m, 1.*U.mm, 2.*U.kg]))  # produces None
    print(lut.evaluate([1.*U.m, 2.*U.mm, 3.*U.kg]))  # produces 0. s
    print(lut.evaluate([2.*U.m, 3.*U.mm, 4.*U.kg]))  # produces 1. s
