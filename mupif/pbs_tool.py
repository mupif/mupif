import subprocess
import os
import time as timemod


def check_if_job_is_done(jobid):
    status = get_job_status(jobid=jobid)
    print("Job %s status is %s" % (str(jobid), status))
    if status == 'Completed' or status == 'Unknown':
        return True
    return False


def wait_until_job_is_done(jobid, checking_frequency=10.):
    job_finished = False
    while job_finished is False:
        status = get_job_status(jobid=jobid)
        print("Job %s status is %s" % (str(jobid), status))
        if status == 'Completed' or status == 'Unknown':
            job_finished = True
        if job_finished is False:
            timemod.sleep(checking_frequency)


def submit_job(command):
    cmmnd = 'qsub %s' % command
    stream = os.popen(cmmnd)
    result = str(stream.read()).strip()
    print("'%s'" % result)
    if result != '':
        return result
    return 'Unknown'


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
                line = line.replace('  ', ' ')
            line = line.strip()
            words = line.split(' ')
            if len(words) >= 2:
                state = words[-2]

                for key, value in states.items():
                    if state == key:
                        return value

    return 'Unknown'
