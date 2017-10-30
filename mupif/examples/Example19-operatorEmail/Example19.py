#!/usr/bin/env python3
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import jsonpickle
import time #for sleep
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

#
# Expected response from operator: E-mail with "CSJ01" (workflow + jobID)
# in the subject line, message body: json encoded dictionary with 'Operator-results' key, e.g.
# {"Operator-results": 3.14}
#

class emailAPI(Application.Application):
    """
    Simple application API that involves operator interaction
    """
    def __init__(self, file):
        super(emailAPI, self).__init__(file)
        # note: "From" should correspond to destination e-mail
        # where the response is received (Operator can reply to the message)
        self.operator = operatorUtil.OperatorEMailInteraction(From='appAPI@gmail.com',
                                                              To='operator@gmail.com',
                                                              smtpHost='smtp.something.com',
                                                              imapHost='imap.gmail.com',
                                                              imapUser='appAPI' )
        self.inputs = {}
        self.outputs = {}
        self.key = 'Operator-results'
    def setProperty(self, property, objectID=0):
        # remember the mapped value
        self.inputs[str(property.propID)] = property
        self.inputs[self.key] = 0.0

    def getProperty(self, propID, time, objectID=0):
        if (self.outputs):
            #unpack & process outputs (expected json encoded data)
            if (propID == PropertyID.PID_Demo_Value):
                if self.key in self.outputs:
                    value = float(self.outputs[self.key])
                    log.info('Found key %s with value %f' %(self.key,value))
                    return Property.Property(value, propID, ValueType.Scalar, time, None, 0)
                else:
                    log.error('Not found key %s in email' % self.key)
                    return None
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        #send email to operator, pack json encoded inputs in the message
        #note workflow and job IDs will be available in upcoming MuPIF version
        self.operator.contactOperator("CS", "J01", jsonpickle.encode(self.inputs))
        responseReceived = False
        # check for response and repeat until received
        while not responseReceived:
            #check response and receive the data
            responseReceived, operatorOutput = self.operator.checkOperatorResponse("CS", "J01")
            #print(responseReceived, operatorOutput.splitlines()[0])
            if responseReceived:
                try:
                    self.outputs = jsonpickle.decode(operatorOutput.splitlines()[0]) #pick up only dictionary to new line
                except Exception as e:
                    log.error(e)
                log.info("Received response from operator %s" % self.outputs)
            else:
                time.sleep(60) #wait
            
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0,'s')


#################################################
#demo code
#################################################
# create instance of application API
app = emailAPI(None)
try:

    # CumulativeConcentration property on input
    p = Property.Property(0.1, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 0.0, None, 0)
    # set concentration as input
    app.setProperty(p)
    # solve (involves operator interaction)
    tstep = TimeStep.TimeStep(0.0, 0.1, 1.0, timeUnits, 1)
    app.solveStep (tstep)
    # get result of the simulation
    r = app.getProperty(PropertyID.PID_Demo_Value, tstep.getTime())
    log.info("Application API return value is %f", r.getValue())
    # terminate app

except Exception as e:
    log.error(e)
finally:
    app.terminate();
