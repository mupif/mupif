import subprocess
from simple_slurm import Slurm


def submit_job(command, job_name, output, cpus_per_task=1):
    slurm = Slurm(
        job_name=job_name,
        output=output,
        cpus_per_task=cpus_per_task
    )
    jobid = slurm.sbatch(command)
    return jobid


# This function analyzes the output of 'qstat [jobid]' command, which has the form:
#
# qstat 182
# Job id              Name             Username        Time Use S Queue
# ------------------- ---------------- --------------- -------- - ---------------
# 182                 TestTask         user            00:00:00 Q debug
#
def get_job_status(jobid):
    result = ''
    try:
        result = str(subprocess.check_output(['qstat', str(jobid)], shell=False, stderr=subprocess.STDOUT))
    except subprocess.SubprocessError:
        pass

    if result != '':
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
                line = line.replace('  ',' ')
            line = line.strip()
            words = line.split(' ')
            if len(words) >= 2:
                state = words[-2]

                for key, value in states.items():
                    if state == key:
                        return value

    return 'Unknown'
