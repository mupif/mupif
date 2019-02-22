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
import logging
log = logging.getLogger()

import mupif.Physics.PhysicalQuantities as PQ

WorkflowSchema = {
    'type': 'object',
    'properties': {
        'Workflow.Name': {'type' : 'string'},#Name of the tool/workflow (e.g.openFOAM). Corresponds to MODA Solver Specification: SOFTWARE TOOL
        'Workflow.ID': {'type' : ['string','integer']},
        'Workflow.Description' : {'type': 'string'},
        'Workflow.Model_refs_ID' : {'type': 'array'},#References to models' IDs
        'Model.Language' : {'type': 'string'},
        'Model.License' : {'type': 'string'},
        'Model.Creator' : {'type': 'string'},
        'Workflow.Version_date' : {'type': 'string'},
        'Workflow.Documentation' : {'type': 'string'},#Where published/documented
        'Workflow.Material' : {'type': 'string'},#What material is simulated
        'Workflow.Manuf_process' : {'type': 'string'},#Manufacturing process or in-service conditions, e.g. Temperature, strain, shear
        'Workflow.Boundary_conditions' : {'type': 'string'},
        'Workflow.Accuracy' : {'type': 'string', 'enum': ['Low', 'Medium', 'High']},
        'Workflow.Sensitivity' : {'type': 'string', 'enum': ['Low', 'Medium', 'High']},
        'Workflow.Complexity' : {'type': 'string', 'enum': ['Low', 'Medium', 'High']},
        'Workflow.Robustness' : {'type': 'string', 'enum': ['Low', 'Medium', 'High']},
        'Workflow.Execution_ID' : {'type': 'string'},
        'Workflow.Estim_time_step' : {'type': 'number'},#Seconds
        'Workflow.Estim_comp_time' : {'type': 'number'},#Seconds
        'Workflow.Estim_execution cost' : {'type': 'number'},#EUR
        'Workflow.Estim_personnel cost' : {'type': 'number'},#EUR
        'Workflow.Required_expertise' : {'type': 'string', 'enum': ['None', 'User', 'Expert']},
        'Workflow.Inputs' : {
            'type': 'array',#List
            'items' : {
                'type': 'object',#Object supplies a dictionary
                'properties': {
                    'ID' : {'type': ['string','integer']},
                    'Name' : { 'type': 'string' },
                    'Description' : {'type': 'string'},
                    'Units' : {'type': 'string'},
                    'Origin' : {'type': 'string', 'enum': ['Experiment', 'User_input', 'Simulated']},
                    'Experimental_details' : {'type': 'string'},
                    'Experimental_record' : {'type': 'string'},
                    'Estimated_std' : {'type': 'number'},
                    'Type' : {'type': 'string'},#e.g. mupif.Property
                    'Type_ID' : {'type': 'string'},
                    'Object_ID' : {'type': 'array'},
                    'Required' : {'type': 'boolean'}
                },
                'required' : ['ID', 'Name', 'Units', 'Origin', 'Type', 'Type_ID', 'Required']
            }
        },
        'Workflow.Outputs' : {
            'type': 'array',
            'items' : {
                'type': 'object',
                'properties': {
                    'ID' : {'type': ['string','integer']},
                    'Name' : { 'type': 'string' },
                    'Description' : {'type': 'string'},
                    'Units' : {'type': 'string'},
                    'Estimated_std' : {'type': 'number'},
                    'Type' : {'type': 'string'},#e.g. mupif.Property
                    'Type_ID' : {'type': 'string'},
                    'Object_ID' : {'type': 'array'}
                },
                'required' : ['ID', 'Name', 'Units', 'Type', 'Type_ID']
            }
        }
    },
    'required' : ['Workflow.Name', 'Workflow.ID', 'Workflow.Description', 'Workflow.Model_refs_ID', 'Workflow.Language', 'Workflow.License', 'Workflow.Creator', 'Workflow.Version_date', 'Workflow.Documentation', 'Workflow.Boundary_conditions', 'Workflow.Accuracy', 'Workflow.Sensitivity', 'Workflow.Complexity', 'Workflow.Robustness', 'Workflow.Execution_ID', 'Workflow.Estim_time_step', 'Workflow.Estim_comp_time', 'Workflow.Estim_execution cost', 'Workflow.Estim_personnel cost', 'Workflow.Required_expertise', 'Workflow.Inputs', 'Workflow.Outputs']
}


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
        self.setMetadata('Workflow.Username', username)
        self.setMetadata('Workflow.Hostname', hostname)
        
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
        self.setMetadata('Workflow.Execution_ID', executionID)
        self.setMetadata('Workflow.Name', self.getApplicationSignature())
        
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
