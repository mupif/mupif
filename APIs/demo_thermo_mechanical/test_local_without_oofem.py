import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
import mupif as mp
import mupif_demo_thermal
import mupif_demo_mechanical


if __name__ == "__main__":
    md = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    ns = mp.pyroutil.connectNameserver()
    daemon = mp.pyroutil.getDaemon(ns)

    tm = mupif_demo_thermal.MUPIF_T_demo()
    tm.initialize(metadata=md)

    sm = mupif_demo_mechanical.MUPIF_M_demo()
    sm.initialize(metadata=md)

    dt = 1.
    targetTime = 1.
    t = 0.
    ts = mp.TimeStep(time=t, dt=dt, targetTime=targetTime, unit=mp.U.s, number=1)
    print("\n==============================\nThermal task:")

    ttop = mp.ConstantProperty(value=300., propID=mp.DataID.PID_Temperature, valueType=mp.ValueType.Scalar, unit=mp.U.deg_C, time=None)
    tbottom = mp.ConstantProperty(value=-300., propID=mp.DataID.PID_Temperature, valueType=mp.ValueType.Scalar, unit=mp.U.deg_C, time=None)
    tm.set(ttop, 'top_edge')
    tm.set(tbottom, 'bottom_edge')

    tm.solveStep(ts)
    tm.finishStep(ts)

    f = tm.get(objectTypeID=mp.DataID.FID_Temperature)
    sm.set(f)

    print("\n==============================\nMechanical task:")
    sm.solveStep(ts)
    sm.finishStep(ts)

    tf = tm.get(mp.DataID.FID_Temperature)
    df = sm.get(mp.DataID.FID_Displacement)
    max_w = sm.get(mp.DataID.PID_maxDisplacement)

    tf.plot2D(fileName='ft.png')
    df.plot2D(fileName='fd.png', fieldComponent=1)
    print(max_w)
