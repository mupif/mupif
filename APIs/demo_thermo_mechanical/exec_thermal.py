#!/usr/bin/python3.10
import os
import sys
import mupif


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_file_full_path = sys.argv[1]
        output_field_full_path = sys.argv[2]
        if os.path.exists(input_file_full_path):
            model = mupif.demo.ThermalModel()
            model.initialize(metadata={'Execution': {'ID': '1', 'Use_case_ID': '1_1', 'Task_ID': '1'}})
            input_file = mupif.PyroFile(filename=input_file_full_path, mode="rb", dataID=mupif.DataID.ID_InputFile)
            model.set(input_file)
            ts = mupif.TimeStep(time=0., dt=1., targetTime=1., unit=mupif.U.s, number=1)
            model.solveStep(ts)
            tf = model.get(mupif.DataID.FID_Temperature, time=ts.getTargetTime())
            tf.toHdf5(output_field_full_path)
            model.terminate()
