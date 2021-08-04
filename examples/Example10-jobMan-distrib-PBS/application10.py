import sys
import os
import Pyro5
import logging
sys.path.extend(['..', '../..'])
import mupif as mp
import time as timemod
import uuid
import pbs_tool

log = logging.getLogger()


@Pyro5.api.expose
class Application10(mp.Model):
    """
    Simple application which sums given time values times 2
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Simple time summator',
            'ID': 'N/A',
            'Description': 'Cummulates given time values times 2',
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
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Time value',
                 'Description': 'Time', 'Units': 's', 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'Summed time value',
                 'Description': 'Cummulative time', 'Units': 's', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.value = 0.
        self.input = 0.

    def initialize(self, file='', workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(file=file, workdir=workdir, metadata=metadata, validateMetaData=validateMetaData)

    def get(self, objectTypeID, time=None, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }

        if objectTypeID == mp.DataID.PID_Time:
            return mp.ConstantProperty(value=(self.value,), propID=mp.DataID.PID_Time, valueType=mp.ValueType.Scalar, unit=mp.U.s, time=time, metadata=md)
        else:
            raise mp.APIError('Unknown property ID')

    def set(self, obj, objectID=0):
        if obj.isInstance(mp.Property):
            if obj.getPropertyID() == mp.DataID.PID_Time:
                self.input = obj.inUnitsOf(mp.U.s).getValue()[0]
            else:
                raise mp.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # this function is designed to run the executable in Torque or Slurm PBS and process the output when the job is finished.

        rp = os.path.realpath(__file__)
        dirname = os.path.dirname(rp)

        # create unique input and output file names (this is specific for each application/executable)
        step_id = uuid.uuid4()
        inpfile = "%s/inp_%s.txt" % (dirname, step_id)
        outfile = "%s/out_%s.txt" % (dirname, step_id)
        #
        # create the input file
        f = open(inpfile, 'w')
        f.write("%f" % self.input)
        f.close()

        #

        # submit the job
        jobid = pbs_tool.submit_job(command=" -v inpfile=\"%s\",outfile=\"%s\",script=\"%s/appexec.py\",dirname=\"%s\" %s/appexec.job -o %s/log.txt -e %s/err.txt" % (inpfile, outfile, dirname, dirname, dirname, dirname, dirname))

        #

        # wait until the job is finished
        # After its completion, the job stays in the list of jobs with 'Completed' status for a while.
        # After that time it is not in the list any more, which results in 'Unknown' state.
        # With 1 minute period of checking the job should be still available in the list.
        pbs_tool.wait_until_job_is_done(jobid=jobid, checking_frequency=1.)

        #

        # process the results (this is specific for each application/executable)
        if os.path.exists(outfile):
            f = open(outfile, 'r')
            read_value = f.readline()
            f.close()
            if read_value != "error":
                self.value += float(read_value)
            else:
                raise mp.apierror.APIError("A problem occured in the solver.")
        else:
            print("File '%s' does not exist." % outfile)
            raise mp.apierror.APIError("The output file does not exist.")

        # delete the temporary input and output files
        if os.path.exists(inpfile):
            os.remove(inpfile)
        if os.path.exists(outfile):
            os.remove(outfile)

    def getCriticalTimeStep(self):
        return 1000.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application10"
