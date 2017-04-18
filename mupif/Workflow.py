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
import Application
import PyroUtil
from . import APIError
from . import log
from . import MetadataKeys
from . import log
from . import TimeStep

@Pyro4.expose
class Workflow(Application.Application):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__ (self, file='', workdir='', targetTime=0.):
        """
        Constructor. Initializes the workflow

        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        """
        super(Workflow, self).__init__(file=file, workdir=workdir)
        self.targetTime = targetTime

        (username, hostname) = PyroUtil.getUserInfo()
        self.setMetadata(MetadataKeys.USERNAME, username)
        self.setMetadata(MetadataKeys.HOSTNAME, hostname)


    def solve(self, runInBackground=False):
        """ 
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, defualt False. If True, the solution will run in background (in separate thread or remotely).

        """
        time = 0.
        timeStepNumber = 0

        while (abs(time-self.targetTime) > 1.e-6):
            dt = self.getCriticalTimeStep()
            time=time+dt
            if (time > self.targetTime):
                         time = targetTime
            timeStepNumber = timeStepNumber+1
            istep=TimeStep.TimeStep(time,dt, timeStepNumber)
        
            log.debug("Step %g: t=%g dt=%g"%(timeStepNumber,time,dt))

            
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

