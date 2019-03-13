# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import os
import Pyro4
import time as timeTime
from . import Model
from . import TimeStep
import copy
import logging
import mupif.Physics.PhysicalQuantities as PQ

log = logging.getLogger()

WorkflowSchema = copy.deepcopy(Model.ModelSchema)
del WorkflowSchema['properties']['Solver']
del WorkflowSchema['properties']['Physics']
WorkflowSchema['properties'].update({'Model_refs_ID': {'type': 'array'}}),  # List of references to contained models
WorkflowSchema['required'] = [
    'Name', 'ID', 'Description', 'Model_refs_ID', 'Execution', 'Inputs', 'Outputs']


@Pyro4.expose
class Workflow(Model.Model):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__(self, targetTime=PQ.PhysicalQuantity(0., 's'), metaData={}):
        """
        Constructor. Initializes the workflow

        :param PhysicalQuantity targetTime: target simulation time
        :param dict metaData: Optionally pass metadata.
        """
        super(Workflow, self).__init__(metaData=metaData)

        # print (targetTime)
        if PQ.isPhysicalQuantity(targetTime):
            self.targetTime = targetTime
        else:
            raise TypeError('targetTime is not PhysicalQuantity')

        self.workflowMonitor = None  # No monitor by default

    def initialize(self, file='', workdir='', executionID='', metaData={}, validateMetaData=True, **kwargs):
        """
        Initializes application, i.e. all functions after constructor and before run.
        
        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        :param str executionID: Optional application execution ID (typically set by workflow)
        :param dict metaData: Optional dictionary used to set up metadata (can be also set by setMetadata() ).
        :param bool validateMetaData: Defines if the metadata validation will be called
        :param named_arguments kwargs: Arbitrary further parameters
        """
        self.updateMetadata(metaData)
        # define futher app metadata 
        self.setMetadata('Execution.ID', executionID)
        # self.setMetadata('Name', self.getApplicationSignature())
        
        self.file = file
        if workdir == '':
            self.workDir = os.getcwd()
        else:
            self.workDir = workdir

        if validateMetaData:
            self.validateMetadata(WorkflowSchema)

    def solve(self, runInBackground=False):
        """ 
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, default False. If True, the solution will run in background (in separate thread or remotely).

        """
        self.setMetadata('Status', 'Running')
        self.setMetadata('Progress', 0.)

        time = PQ.PhysicalQuantity(0., 's')
        timeStepNumber = 0
        
        while abs(time.inUnitsOf('s').getValue()-self.targetTime.inUnitsOf('s').getValue()) > 1.e-6:
            dt = self.getCriticalTimeStep()
            time = time+dt
            if time > self.targetTime:
                time = self.targetTime
            timeStepNumber = timeStepNumber+1
            istep = TimeStep.TimeStep(time, dt, self.targetTime, n=timeStepNumber)
        
            log.debug("Step %g: t=%g dt=%g"%(timeStepNumber, time.inUnitsOf('s').getValue(), dt.inUnitsOf('s').getValue()))

            # Estimate progress
            self.setMetadata('Progress', 100*time.inUnitsOf('s').getValue()/self.targetTime.inUnitsOf('s').getValue())
            
            self.solveStep(istep)
            self.finishStep(istep)
        self.setMetadata('Status', 'Finished')
        self.setMetadata('Date_time_end', timeTime.strftime("%Y-%m-%d %H:%M:%S", timeTime.gmtime()))
        self.terminate()

    def getAPIVersion(self):
        """
        :return: Returns the supported API version
        :rtype: str, int
        """
    def getApplicationSignature(self):
        """
        Get application signature.

        :return: Returns the application identification
        :rtype: str
        """
        return 'Workflow'
    
    def updateStatus(self, status, progress=0):
        """
        Updates the workflow status. The status is submitted to workflow monitor. The self.workflowMonitor
        should be (proxy) to workflowManager
        :param str status: string describing the workflow status (initialized, running, failed, finished)
        :param int progress: integer number indicating execution progress (in percent)
        """
        # PyroUtil.connectNameServer(nshost, nsport, hkey)
        # try:
        #     uri = ns.lookup(workflowMonitorName)
        #     workflowMonitor = Pyro4.Proxy(uri)
        # except Exception as e:
        #     log.error("Cannot find workflow monitor")
        #     return # do not raise, silently continue without updating status

        if self.workflowMonitor:
            date = timeTime.strftime("%d %b %Y %H:%M:%S", timeTime.gmtime())
            # metadata = {WorkflowMonitor.WorkflowMonitorKeys.Status: status,
            # WorkflowMonitor.WorkflowMonitorKeys.Progress: progress,
            # WorkflowMonitor.WorkflowMonitorKeys.Date: date}
            metadata = {'WorkflowMonitor.Status': status,
                        'WorkflowMonitor.Progress': progress,
                        'WorkflowMonitor.Date': date}
            
            try:
                self.workflowMonitor.updateMetadata(self.getMetadata('WorkflowMonitor.ComponentID'), metadata)
                # could not use nameserver metadata capability, as this requires workflow to be registered
                # thus Pyro daemon is required

                log.debug(self.getMetadata('WorkflowMonitor.ComponentID')+": Updated status to " + status + ", progress=" + str(progress))
            except Exception as e:
                log.exception("Connection to workflow monitor broken")
                raise e
