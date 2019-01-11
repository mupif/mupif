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
from . import Application
from . import PyroUtil
from . import APIError
from . import MetadataKeys
from . import TimeStep
from . import WorkflowMonitor
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])

@Pyro4.expose
class Workflow(Application.Application):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__ (self, file='', workdir='', executionID = None, targetTime=PQ.PhysicalQuantity(0., 's')):
        """
        Constructor. Initializes the workflow

        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        :param str executionID: Optional workflow execution ID (typically set by scheduler)
        :param PhysicalQuantity targetTime: target simulation time
        """
        super(Workflow, self).__init__(file=file, workdir=workdir, executionID=executionID)

        #print (targetTime)
        if (PQ.isPhysicalQuantity(targetTime)):
            self.targetTime = targetTime
        else:
            raise TypeError ('targetTime is not PhysicalQuantity')

        self.workflowMonitor = None # no monitor by default

        # define workflow metadata
        (username, hostname) = PyroUtil.getUserInfo()
        self.setMetadata(MetadataKeys.USERNAME, username)
        self.setMetadata(MetadataKeys.HOSTNAME, hostname)
        

    def solve(self, runInBackground=False):
        """ 
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, default False. If True, the solution will run in background (in separate thread or remotely).

        """
        time = PQ.PhysicalQuantity(0., timeUnits)
        timeStepNumber = 0

        while (abs(time.inUnitsOf(timeUnits).getValue()-self.targetTime.inUnitsOf(timeUnits).getValue()) > 1.e-6):
            dt = self.getCriticalTimeStep()
            time=time+dt
            if (time > self.targetTime):
                         time = self.targetTime
            timeStepNumber = timeStepNumber+1
            istep=TimeStep.TimeStep(time, dt, self.targetTime, n=timeStepNumber)
        
            log.debug("Step %g: t=%g dt=%g"%(timeStepNumber,time.inUnitsOf(timeUnits).getValue(),dt.inUnitsOf(timeUnits).getValue()))

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
    
    def updateStaus(self, status, progress=0):
        """
        Updates the workflow status. The status is subnitted to workflow monitor. The self.workflowMonitor
        should be (proxy) to workflowManager
        :param str status: string describing the workflow status (initialized, running, failed, finished)
        :param int progress: integer number indicating execution progress (in percent)
        """
        #PyroUtil.connectNameServer(nshost, nsport, hkey)
        #try:
        #    uri = ns.lookup(workflowMonitorName)
        #    workflowMonitor = Pyro4.Proxy(uri)
        #except Exception as e:
        #    log.error("Cannot find workflow monitor")
        #    return # do not raise, silently continue without updating status

        if (self.workflowMonitor):
            date = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
            metadata = {WorkflowMonitor.WorkflowMonitorKeys.Status: status,
                        WorkflowMonitor.WorkflowMonitorKeys.Progress: progress,
                        WorkflowMonitor.WorkflowMonitorKeys.Date: date}
            try:
                self.workflowMonitor.updateMetadata(self.getMetadata(MetadataKeys.ComponentID), metadata)
                # could not use nameserver metadata capability, as this requires workflow to be registered
                # thus Pyro daemon is required

                log.debug(self.getMetadata(MetadataKeys.ComponentID)+": Updated status to " + status + ", progress=" + str(progress))
            except Exception as e:
                log.exception("Connection to workflow monitor broken")
                raise e

    