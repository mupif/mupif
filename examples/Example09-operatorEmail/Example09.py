#!/usr/bin/env python3
import sys
sys.path.extend(['..', '../..'])
from mupif import *
import mupif as mp
import jsonpickle
import time  # for sleep
import logging
log = logging.getLogger()

#
# Expected response from operator: E-mail with "CSJ01" (workflow + jobID)
# in the subject line, message body: json encoded dictionary with 'Operator-results' key, e.g.
# {"Operator-results": 3.14}
#


class EmailAPI(model.Model):
    """
    Simple application API that involves operator interaction
    """
    def __init__(self):
        super().__init__()
        # note: "From" should correspond to destination e-mail
        # where the response is received (Operator can reply to the message)
        self.operator = operatorutil.OperatorEMailInteraction(From='appAPI@gmail.com',
                                                              To='operator@gmail.com',
                                                              smtpHost='smtp.something.com',
                                                              imapHost='imap.gmail.com',
                                                              imapUser='appAPI')
        self.inputs = {}
        self.outputs = {}
        self.key = 'Operator-results'

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        MD = {
            'Name': 'Email operator application',
            'ID': 'N/A',
            'Description': 'Sending email with input and receiving email with results',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Unknown',
                'Language': 'Unknown',
                'License': 'Unknown',
                'Creator': 'Unknown',
                'Version_date': '02/2019',
                'Type': 'Summator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'Unknown',
                'Sensitivity': 'Unknown',
                'Complexity': 'Unknown',
                'Robustness': 'Unknown'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_CumulativeConcentration', 'Name': 'Concentration', 'Description': 'Concentration', 'Units': 'kg/m**3', 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep"}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Demo_Value', 'Name': 'Demo value',
                 'Description': 'Demo value', 'Units': 'dimensionless', 'Origin': 'Simulated'}]
        }
        self.updateMetadata(MD)
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Property):
            # remember the mapped value
            self.inputs[str(obj.propID)] = property
            self.inputs[self.key] = 0.0

    def get(self, objectTypeID, time=None, objectID=""):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        if self.outputs:
            # unpack & process outputs (expected json encoded data)
            if objectTypeID == DataID.PID_Demo_Value:
                if self.key in self.outputs:
                    value = float(self.outputs[self.key])
                    log.info('Found key %s with value %f' % (self.key, value))
                    return property.ConstantProperty(
                        value=value, propID=objectTypeID, valueType=ValueType.Scalar, unit=mp.U.none, time=time, metadata=md)
                else:
                    log.error('Not found key %s in email' % self.key)
                    return None
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # send email to operator, pack json encoded inputs in the message
        # note workflow and job IDs will be available in upcoming MuPIF version
        self.operator.contactOperator("CS", "J01", jsonpickle.encode(self.inputs))
        responseReceived = False
        # check for response and repeat until received
        while not responseReceived:
            # check response and receive the data
            responseReceived, operatorOutput = self.operator.checkOperatorResponse("CS", "J01")
            # print(responseReceived, operatorOutput.splitlines()[0])
            if responseReceived:
                try:
                    self.outputs = jsonpickle.decode(operatorOutput.splitlines()[0])  # pick up only dictionary to new line
                except Exception as e:
                    log.error(e)
                log.info("Received response from operator %s" % self.outputs)
            else:
                time.sleep(60)  # wait
            
    def getCriticalTimeStep(self):
        return 1.*mp.U.s


#################################################
# demo code
#################################################
# create instance of application API
app = EmailAPI()

executionMetadata = {
    'Execution': {
        'ID': '1',
        'Use_case_ID': '1_1',
        'Task_ID': '1'
    }
}

app.initialize(metadata=executionMetadata)

# CumulativeConcentration property on input
p = property.ConstantProperty(value=0.1, propID=DataID.PID_CumulativeConcentration, valueType=ValueType.Scalar, unit=mp.U['kg/m**3'])
# set concentration as input
app.set(p)
# solve (involves operator interaction)
tstep = timestep.TimeStep(time=0.0, dt=0.1, targetTime=1.0, unit=mp.U.s, number=1)
app.solveStep (tstep)
# get result of the simulation
r = app.get(DataID.PID_Demo_Value, tstep.getTime())
log.info("Application API return value is %f", r.getValue())
# terminate app

