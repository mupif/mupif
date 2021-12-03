import sys
import Pyro5
sys.path.extend(['..', '../..'])
import logging
log = logging.getLogger()

from exconfig import ExConfig
import threading
cfg = ExConfig()
import mupif as mp

threading.current_thread().setName('ex10-main')

#

# locate nameserver
ns = mp.pyroutil.connectNameServer(cfg.nshost, cfg.nsport)
# connect to JobManager running on (remote) server and create a tunnel to it
jobMan = mp.pyroutil.connectJobManager(ns, cfg.jobManName)
log.info('Connected to JobManager')
model1 = None

try:
    model1 = mp.pyroutil.allocateApplicationWithJobManager(ns=ns, jobMan=jobMan)
    log.info(model1)
except Exception as e:
    log.exception(e)

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

model1.initialize(metadata=executionMetadata)

checkval = None

var_time = 0.*mp.U.s
target_time = 2.*mp.U.s

compute = True
timestep_number = 0

while compute:
    timestep_number += 1

    dt = min([1. * mp.U.s, model1.getCriticalTimeStep()])
    var_time = min([var_time.inUnitsOf('s').getValue() + dt.inUnitsOf('s').getValue(), target_time.inUnitsOf('s').getValue()]) * mp.U.s

    if var_time.inUnitsOf('s').getValue() + 1.e-6 > target_time.inUnitsOf('s').getValue():
        compute = False

    timestep = mp.timestep.TimeStep(time=var_time, dt=dt, targetTime=target_time, number=timestep_number)

    # prepare the input value as ConstantProperty
    time_param = mp.ConstantProperty(value=(var_time.inUnitsOf(mp.U.s).getValue(),), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=None)
    # set the input value to the model
    model1.set(time_param)
    # the model solves a computational step
    model1.solveStep(tstep=timestep)
    # get the output value of the model
    time_result = model1.get(mp.DataID.PID_Time, timestep.getTime())

    #

    # testing purposes
    checkval = time_result.getValue(timestep.getTime())[0]

# terminate
model1.terminate()

#

# testing part
print(checkval)
if checkval is not None and abs(checkval - 6.) <= 1.e-4:
    print("Test OK")
    log.info("Test OK")
else:
    print("Test FAILED")
    log.error("Test FAILED")

