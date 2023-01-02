import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
import mupif as mp
import oofem


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

    ot = oofem.OOFEM()
    ot.initialize(metadata=md)
    inp_file_t = mp.PyroFile(filename='./testt.oofem.in', mode="rb", dataID=mp.DataID.ID_InputFile)
    daemon.register(inp_file_t)
    ot.set(inp_file_t)

    # om = oofem.OOFEM()
    # ot.initialize(metadata=md)
    # inp_file_m = mp.PyroFile(filename='./testm.oofem.in', mode="rb", dataID=mp.DataID.ID_InputFile)
    # daemon.register(inp_file_m)
    # om.set(inp_file_m)

    dt = 0.1
    targetTime = 1.
    for istep in range(10):
        t = istep * dt
        ts = mp.TimeStep(time=t, dt=dt, targetTime=targetTime, unit=mp.U.s, number=istep)

        ot.solveStep(ts)
        ot.finishStep(ts)

        # om.solveStep(ts)
        # om.finishStep(ts)
