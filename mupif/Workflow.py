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

from builtins import object
import os
import Pyro4
import time
from . import Model
from . import PyroUtil
from . import APIError
from . import MetadataKeys
from . import TimeStep
from . import WorkflowMonitor
import copy
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ

WorkflowSchema = copy.deepcopy(Model.ModelSchema)
WorkflowSchema['required'] = ['Name', 'ID', 'Description', 'Representation', 'Language', 'License', 'Creator', 'Version_date', 'Documentation', 'Model_refs_ID', 'Boundary_conditions', 'Accuracy', 'Sensitivity', 'Complexity', 'Robustness', 'Execution_ID', 'Estim_time_step', 'Estim_comp_time', 'Estim_execution cost', 'Estim_personnel cost', 'Required_expertise', 'Inputs', 'Outputs']


@Pyro4.expose
class Workflow(Model.Model):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__(self, targetTime=PQ.PhysicalQuantity(0., 's')):
        """
        Constructor. Initializes the workflow

        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        :param str executionID: Optional workflow execution ID (typically set by scheduler)
        :param PhysicalQuantity targetTime: target simulation time
        """
        super(Workflow, self).__init__()

        # print (targetTime)
        if PQ.isPhysicalQuantity(targetTime):
            self.targetTime = targetTime
        else:
            raise TypeError('targetTime is not PhysicalQuantity')

        self.workflowMonitor = None  # no monitor by default

        # define workflow metadata
        (username, hostname) = PyroUtil.getUserInfo()
        self.setMetadata('Username', username)
        self.setMetadata('Hostname', hostname)
        
    def initialize(self, file='', workdir='', executionID='None', metaData={}, **kwargs):
        """
        Initializes application, i.e. all functions after constructor and before run.
        
        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        :param str executionID: Optional application execution ID (typically set by workflow)
        :param dict metadata: Optional dictionary used to set up metadata (can be also set by setMetadata() ).
        :param named_arguments kwargs: Arbitrary further parameters 
        """
        self.metadata.update(metaData)
        # define futher app metadata 
        self.setMetadata('Execution_ID', executionID)
        self.setMetadata('Name', self.getApplicationSignature())
        
        self.file = file
        if workdir == '':
            self.workDir = os.getcwd()
        else:
            self.workDir = workdir
        
        self.validateMetadata(WorkflowSchema)

    def solve(self, runInBackground=False):
        """ 
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, default False. If True, the solution will run in background (in separate thread or remotely).

        """
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

            self.solveStep(istep)
            self.finishStep(istep)
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
        return "Workflow"
    
    def updateStatus(self, status, progress=0):
        """
        Updates the workflow status. The status is subnitted to workflow monitor. The self.workflowMonitor
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
            date = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
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
