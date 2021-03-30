import sys
sys.path.extend(['..', '../..'])
from mupif import *
import logging
log = logging.getLogger()

from exconfig import ExConfig
import threading
cfg = ExConfig()
import mupif as mp


threading.current_thread().setName('ex02-main')


class Example10(mp.Model):
    """
    Simple application that generates a property with a value equal to actual time
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Simple application example',
            'ID': 'N/A',
            'Description': 'Cummulates time steps^3',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Python script',
                'Language': 'Python3',
                'License': 'LGPL',
                'Creator': 'Borek',
                'Version_date': '02/2019',
                'Type': 'Summator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'High',
                'Sensitivity': 'High',
                'Complexity': 'Low',
                'Robustness': 'High'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time_step', 'Name': 'Time step',
                 'Description': 'Time step', 'Units': 's',
                 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == mp.PropertyID.PID_Time_step:
            return property.ConstantProperty(
                value=(self.value,), propID=mp.PropertyID.PID_Time_step, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise apierror.APIError('Unknown property ID')

    def initialize(self, file='', workdir='', metadata={}, validateMetaData=True):
        super().initialize(file, workdir, metadata, validateMetaData)

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf('s').getValue()
        self.value = 1.0*time

    def getCriticalTimeStep(self):
        return 2.*mp.U.s

    def getAsssemblyTime(self, tstep):
        return tstep.getTime()

# Example10 is local, create its instance
app1 = Example10()


time = 0.
timestepnumber = 0
targetTime = 2.0


# locate nameserver
ns = pyroutil.connectNameServer(cfg.nshost, cfg.nsport)
# connect to JobManager running on (remote) server and create a tunnel to it
jobMan = mp.pyroutil.connectJobManager(ns, cfg.jobManName)
log.info('Connected to JobManager')
app2 = None

try:
    app2 = mp.pyroutil.allocateApplicationWithJobManager(ns=ns, jobMan=jobMan)
    log.info(app2)
except Exception as e:
    log.exception(e)

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app1.initialize(metadata=executionMetadata)
app2.initialize(metadata=executionMetadata)

prop = None
istep = None

if True:  # one step
    # determine critical time step
    dt2 = app2.getCriticalTimeStep().inUnitsOf(mp.U.s).getValue()
    dt = min(app1.getCriticalTimeStep().inUnitsOf(mp.U.s).getValue(), dt2)
    # update time
    time = time+dt
    if time > targetTime:
        # make sure we reach targetTime at the end
        time = targetTime
    timestepnumber = timestepnumber+1
    log.debug("Step: %d %f %f" % (timestepnumber, time, dt))
    # create a time step
    istep = mp.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mp.U.s, number=timestepnumber)

    try:
        # solve problem 1
        app1.solveStep(istep)
        # handshake the data
        c = app1.getProperty(mp.PropertyID.PID_Time_step, app2.getAssemblyTime(istep))
        app2.setProperty(c)
        app2.solveStep(istep)

        prop = app2.getProperty(mp.PropertyID.PID_Time, istep.getTime())

        atime = app2.getAssemblyTime(istep)
        log.debug("Time: %5.2f app1-time step %5.2f, app2-cummulative time %5.2f" % (
            atime.getValue(), c.getValue(atime)[0], prop.getValue(atime)[0]))

    except apierror.APIError as e:
        log.error("Following API error occurred: %s" % e)

print(prop.getValue(istep.getTime())[0])
if prop is not None and istep is not None and abs(prop.getValue(istep.getTime())[0]-8.) <= 1.e-4:
    log.info("Test OK")
else:
    log.error("Test FAILED")
    sys.exit(1)

# terminate
app1.terminate()
app2.terminate()
