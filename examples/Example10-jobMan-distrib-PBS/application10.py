import sys
import os
import Pyro5
import logging
sys.path.extend(['..', '../..'])
import mupif as mp
from simple_slurm import Slurm
import time as timemod
import uuid
import pbs_tool_slurm

log = logging.getLogger()


@Pyro5.api.expose
class Application10(mp.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Simple application cummulating time steps',
            'ID': 'N/A',
            'Description': 'Cummulates time steps',
            'Version_date': '02/2019',
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Time', 'Name': 'Cummulative time',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.0
        self.count = 0
        self.contrib = mp.ConstantProperty(value=(0.,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=0*mp.U.s)

    def initialize(self, file='', workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(file=file, workdir=workdir, metadata=metadata, validateMetaData=validateMetaData)

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if propID == mp.PropertyID.PID_Time:
            return mp.ConstantProperty(value=(self.value,), propID=mp.PropertyID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise mp.APIError('Unknown property ID')

    def setProperty(self, prop, objectID=0):
        if prop.getPropertyID() == mp.PropertyID.PID_Time_step:
            # remember the mapped value
            self.contrib = prop
        else:
            raise mp.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # this function is designed to run the executable in Slurm PBS and process the output when the job is finished.

        # create unique input and output file names
        step_id = uuid.uuid4()
        inpfile = "inp_%s.txt" % step_id
        outfile = "out_%s.txt" % step_id

        inputvalue = self.contrib.inUnitsOf(mp.U.s).getValue(tstep.getTime())[0]

        # prepare the input file
        f = open(inpfile, 'w')
        f.write("%f" % inputvalue)
        f.close()

        # submit the job
        rp = os.path.realpath(__file__)
        dirname = os.path.dirname(rp)
        jobid = pbs_tool_slurm.submit_job(
            command='python %s/appexec.py %s %s' % (dirname, inpfile, outfile),
            job_name='MupifExample10',
            output=dirname + '/%A_%a.out',
            cpus_per_task=1
        )

        # wait until the job is finished
        # After its completion, the job stays in the list of jobs with 'Completed' status for a while.
        # After that time it is not in the list any more, which results in 'Unknown' state.
        # With 1 minute period of checking the job should be still available in the list.
        status = ''
        job_finished = False
        while job_finished is False:
            status = pbs_tool_slurm.get_job_status(jobid=jobid)
            print("Job %d status is %s" % (jobid, status))
            if status == 'Completed' or status == 'Unknown':
                job_finished = True
            if job_finished is False:
                timemod.sleep(10.)

        # process the results
        if os.path.exists(outfile):
            f = open(outfile, 'r')
            read_value = f.readline()
            f.close()
            if read_value != "error":
                self.value = float(read_value)
            else:
                raise mp.apierror.APIError("A problem occured in the solver.")
        else:
            raise mp.apierror.APIError("The output file does not exist.")

        self.count = self.count+1

        # delete the files
        if os.path.exists(inpfile):
            os.remove(inpfile)
        if os.path.exists(outfile):
            os.remove(outfile)

    def getCriticalTimeStep(self):
        return 3.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application10"
