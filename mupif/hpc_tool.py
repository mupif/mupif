import os
import time as timemod
from enum import Enum


def ssh_command(ssh_login, command):
    full_command = f"ssh {ssh_login} \"{command}\""
    stream = os.popen(full_command)
    result = str(stream.read()).strip()
    return result


def local_command(command):
    stream = os.popen(command)
    result = str(stream.read()).strip()
    return result


# ==================================================


class SchedulingType(Enum):
    TORQUE = 1
    SLURM = 2


class HPCTool:
    def __init__(self, scheduling_type, ssh_login=None):
        """
        :param SchedulingType scheduling_type: TORQUE or SLURM
        :param string ssh_login: e.g. user@url.com If None, then local.
        """
        self.scheduling_type = scheduling_type
        self.ssh_login = ssh_login

    def check_if_job_is_done(self, jobid):
        if self.scheduling_type == SchedulingType.TORQUE:
            return self._check_if_job_is_done_torque(jobid=jobid)
        if self.scheduling_type == SchedulingType.SLURM:
            return self._check_if_job_is_done_slurm(jobid=jobid)

    def wait_until_job_is_done(self, jobid, checking_frequency=10.):
        if self.scheduling_type == SchedulingType.TORQUE:
            return self._wait_until_job_is_done_torque(jobid=jobid, checking_frequency=checking_frequency)
        if self.scheduling_type == SchedulingType.SLURM:
            return self._wait_until_job_is_done_slurm(jobid=jobid, checking_frequency=checking_frequency)

    def submit_job(self, command, directory=None):
        if self.scheduling_type == SchedulingType.TORQUE:
            return self._submit_job_torque(command=command, directory=directory)
        if self.scheduling_type == SchedulingType.SLURM:
            return self._submit_job_slurm(command=command, directory=directory)

    def get_job_status(self, jobid):
        if self.scheduling_type == SchedulingType.TORQUE:
            return self._get_job_status_torque(jobid=jobid)
        if self.scheduling_type == SchedulingType.SLURM:
            return self._get_job_status_slurm(jobid=jobid)

    # ==================================================
    # TORQUE ===========================================
    # ==================================================

    def _submit_job_torque(self, command, directory=None):
        full_command = '' if directory is None else f"cd {directory};"
        full_command = f"{full_command}qsub {command}"
        if self.ssh_login:
            result = ssh_command(ssh_login=self.ssh_login, command=full_command)
        else:
            result = local_command(command=full_command)
        result = result.strip()
        if result:
            return result
        return 'Unknown'

    # This function analyzes the output of 'qstat [jobid]' command, which has the form:
    #
    # qstat 182
    # Job id              Name             Username        Time Use S Queue
    # ------------------- ---------------- --------------- -------- - ---------------
    # 182                 TestTask         user            00:00:00 Q debug
    #
    def _get_job_status_torque(self, jobid):
        command = f"qstat {jobid}"
        if self.ssh_login:
            result = ssh_command(ssh_login=self.ssh_login, command=command)
        else:
            result = local_command(command=command)

        if result:
            states = {
                'C': 'Completed',
                'E': 'Exiting',
                'H': 'Held',
                'Q': 'Pending',
                'R': 'Running',
                'T': 'Transfering',
                'W': 'Waiting',
                'S': 'Suspended'
            }

            lines = result.split('\\n')
            if len(lines) >= 3:
                line = lines[2]
                while '  ' in line:
                    line = line.replace('  ', ' ')
                line = line.strip()
                words = line.split(' ')
                if len(words) >= 2:
                    state = words[-2]

                    for key, value in states.items():
                        if state == key:
                            return value
                    return state

        return 'Unknown'

    def _check_if_job_is_done_torque(self, jobid):
        status = self._get_job_status_torque(jobid=jobid)
        print("Job %s status is %s" % (str(jobid), status))
        if status == 'Completed' or status == 'Unknown':
            return True
        return False

    def _wait_until_job_is_done_torque(self, jobid, checking_frequency=10.):
        job_finished = False
        while job_finished is False:
            status = self._get_job_status_torque(jobid=jobid)
            print("Job %s status is %s" % (str(jobid), status))
            if status == 'Completed' or status == 'Unknown':
                job_finished = True
            if job_finished is False:
                timemod.sleep(checking_frequency)


    # ==================================================
    # SLURM ============================================
    # ==================================================

    def _submit_job_slurm(self, command, directory=None):
        full_command = '' if directory is None else f"cd {directory};"
        full_command = f"{full_command}sbatch {command}"
        if self.ssh_login:
            result = ssh_command(ssh_login=self.ssh_login, command=full_command)
        else:
            result = local_command(command=full_command)
        result = result.strip()
        if result.startswith('Submitted batch job '):
            return result.replace('Submitted batch job ', '')
        return 'Unknown'

    # This function analyzes the output of 'scontrol show job [jobid]' command, which has the form:
    # scontrol show job 232150
    # JobId=232150 JobName=MuPIF_test
    #    UserId=stanislavsulc(9386) GroupId=stanislavsulc(11206) MCS_label=N/A
    #    Priority=206912915 Nice=0 Account=fta-23-16 QOS=2469_3899
    #    JobState=COMPLETED Reason=None Dependency=(null)
    #    ...
    # OR
    # slurm_load_jobs error: Invalid job id specified
    #
    def _get_job_status_slurm(self, jobid):
        command = f"scontrol show job {jobid}"
        if self.ssh_login:
            result = ssh_command(ssh_login=self.ssh_login, command=command)
        else:
            result = local_command(command=command)
        parts = result.split(' ')
        for p in parts:
            if p.startswith('JobState='):
                status = p.replace('JobState=', '')
                return status
        return 'Unknown'

    def _check_if_job_is_done_slurm(self, jobid):
        status = self._get_job_status_slurm(jobid=jobid)
        print("Job %s status is %s" % (str(jobid), status))
        if status == 'COMPLETED' or status == 'FAILED' or status == 'Unknown':
            return True
        return False

    def _wait_until_job_is_done_slurm(self, jobid, checking_frequency=10.):
        job_finished = False
        while job_finished is False:
            status = self._get_job_status_slurm(jobid=jobid)
            print("Job %s status is %s" % (str(jobid), status))
            if status == 'COMPLETED' or status == 'FAILED' or status == 'Unknown':
                job_finished = True
            if job_finished is False:
                timemod.sleep(checking_frequency)
