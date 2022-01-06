import sys
sys.path.extend(['..', '../..'])
import mupif as mp


if __name__ == '__main__':
    mdpds = mp.MultiDimPropertyDataStore()

    mdpds.setXData([0., 1., 2., 3.], mp.U.m)

    mdpds.addYData([(5.,), (6.,), (7.,), (8.,)], mp.U.s, mp.DataID.PID_Time, mp.ValueType.Scalar)
    mdpds.addYData([(15.,), (16.,), (17.,), (18.,)], mp.U.m, mp.DataID.PID_Length, mp.ValueType.Scalar)

    print(mdpds.evaluate(1.5*mp.U.m, mp.DataID.PID_Time))  # produces property with value (6.5,) s
    print(mdpds.evaluate(1.5*mp.U.m, mp.DataID.PID_Length))  # produces property with value (16.5,) m
