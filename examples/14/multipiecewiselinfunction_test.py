import sys
sys.path.extend(['..', '../..'])
import mupif as mp


if __name__ == '__main__':
    mplf = mp.MultiPiecewiseLinFunction()

    mplf.setXData([0., 1., 2., 3.], mp.U.m)

    mplf.addYData([(5.,), (6.,), (7.,), (8.,)], mp.U.s, mp.DataID.PID_Time, mp.ValueType.Scalar)
    mplf.addYData([(15.,), (16.,), (17.,), (18.,)], mp.U.m, mp.DataID.PID_Length, mp.ValueType.Scalar)

    print(mplf.evaluate(1.5*mp.U.m, mp.DataID.PID_Time))  # produces property with value (6.5,) s
    print(mplf.evaluate(1.5*mp.U.m, mp.DataID.PID_Length))  # produces property with value (16.5,) m
