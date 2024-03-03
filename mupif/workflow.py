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
import Pyro5
import numpy
import copy
import logging
import importlib
import pydantic
import time as timeTime

from . import model
from . import timestep
from . import units
from . import Property
from . import DataID
from . import U
from . import pyroutil
from .meta import WorkflowMeta

log = logging.getLogger()


workflow_input_targetTime_metadata = {
    'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'targetTime', 'Description': 'Target time value',
    'Units': 's', 'Origin': 'User_input', 'Required': False, 'Set_at': 'initialization', 'Obj_ID': 'targetTime', 'ValueType': 'Scalar'
}
workflow_input_dt_metadata = {
    'Type': 'mupif.Property', 'Type_ID': 'mupif.DataID.PID_Time', 'Name': 'dt', 'Description': 'Timestep length',
    'Units': 's', 'Origin': 'User_input', 'Required': False, 'Set_at': 'initialization', 'Obj_ID': 'dt', 'ValueType': 'Scalar'
}


@Pyro5.api.expose
class Workflow(model.Model):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__(self, *, metadata=None):
        """
        Constructor. Initializes the workflow

        :param dict metadata: Optionally pass metadata.
        """
        super().__init__(metadata=metadata)

        self.workflowMonitor = None  # No monitor by default
        self._models = {}
        self._jobmans = {}
        self._exec_targetTime = 1.*units.U.s
        self._exec_dt = None

    def _generateNewModelName(self, base='m'):
        i = 0
        while True:
            i += 1
            name = base + '_' + str(i)
            if name not in self._models.keys():
                return name

    def _allocateModel(self, *, name, modulename, classname, jobmanagername):
        if name:
            if jobmanagername:
                ns = pyroutil.connectNameserver()
                self._jobmans[name] = pyroutil.connectJobManager(ns, jobmanagername)
                # remoteLogUri must be known before the model is spawned (too late in _model.initialize)
                self._models[name] = pyroutil.allocateApplicationWithJobManager(ns=ns, jobMan=self._jobmans[name], remoteLogUri=self.getMetadata('Execution.Log_URI', ''))
                return self._models[name]
            elif classname and modulename:
                moduleImport = importlib.import_module(modulename)
                model_class = getattr(moduleImport, classname)
                self._models[name] = model_class()
                return self._models[name]
        return None
    
    def _allocateModelWithMetadata(self, *, name, modulename, classname, modelConfiguration):
        if name:
            if modelConfiguration:
                ns = pyroutil.connectNameserver()
                metadata = modelConfiguration['RequiredModelMetadata'].copy()
                optionalMetaData = modelConfiguration['OptionalModelMetadata'].copy()
                metadata.add(name)
                #print ("_allocateModelWithMetadata:")
                #print(name, metadata, optionalMetaData)
                self._jobmans[name] = pyroutil.connectModelServerWithMetadata(ns, metadata, optionalMetaData )
                #print (self._jobmans[name])
                # remoteLogUri must be known before the model is spawned (too late in _model.initialize)
                self._models[name] = pyroutil.allocateApplicationWithJobManager(ns=ns, jobMan=self._jobmans[name], remoteLogUri=self.getMetadata('Execution.Log_URI', ''))
                #print (self._models[name])
                return self._models[name]
            elif classname and modulename:
                moduleImport = importlib.import_module(modulename)
                model_class = getattr(moduleImport, classname)
                self._models[name] = model_class()
                return self._models[name]
        return None

    def _allocateModelByName(self, *, name, name_new=None):
        if name_new is None:
            name_new = self._generateNewModelName(base=name)
            # name_new = name
            # if name_new in self._models.keys():
            #     name_new = self._generateNewModelName(base=name)
        else:
            if name_new in self._models.keys():
                name_new = self._generateNewModelName(base=name)
        model_info = None
        for m in self.metadata['Models']:
            if m['Name'] == name:
                model_info = m
        if model_info is not None:
            new_model = self._allocateModel(name=name_new, modulename=model_info.get('Module', ''), classname=model_info.get('Class', ''), jobmanagername=model_info.get('Jobmanager', ''))
            return new_model, name_new

    def _allocateAllModels(self):
        # for model_info in self.metadata['Models']:
        #     if model_info.get('Instantiate', True):
        #         self._allocateModelByName(name=model_info.get('Name', ''), name_new=model_info.get('Name', ''))
        executionProfile = -1
        print (self.metadata['Execution'])
        if 'ExecutionProfileIndx' in self.metadata['Execution']:
            executionProfile = self.metadata['Execution']['ExecutionProfileIndx']

        print("Workflow::executionProfile #%d"%(executionProfile,))
        for model_info in self.metadata['Models']:
            if model_info.get('Instantiate', True):
                name=model_info.get('Name', '')
                if (executionProfile < 0):
                    self._allocateModel(name, modulename=model_info.get('Module', ''), classname=model_info.get('Class', ''), jobmanagername=model_info.get('Jobmanager', ''))
                else:
                    executionProfile = self.metadata['ExecutionProfiles'][executionProfile]
                    mep = None
                    for ep in executionProfile['Models']:
                        if (ep['Name'] == name):
                            mep = ep
                            break
                    if (mep):
                        self._allocateModelWithMetadata(name=name, modulename=model_info.get('Module', ''), classname=model_info.get('Class', ''), modelConfiguration=mep)
                    else:
                        log.fatal("Workflow::_allocateModels: model (%s) execution profile missing for configuration %d"%(name, executionProfile))

    def _initializeAllModels(self):
        _md = self._getInitializationMetadata()
        for _model in self._models.values():
            # print("Workflow calls initialize of " + _model.__class__.__name__)
            _model.initialize(metadata=_md)

    def _getInitializationMetadata(self):
        return {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID'),
                'Log_URI': self.getMetadata('Execution.Log_URI', '')
            }
        }

    def getModel(self, name):
        if name in self._models.keys():
            return self._models[name]
        return None

    def getJobManager(self, name):
        if name in self._jobmans.keys():
            return self._jobmans[name]
        return None

    def initialize(self, *, workdir='', metadata=None, validateMetaData=True, **kwargs):
        """
        Initializes application, i.e. all functions after constructor and before run.

        :param str workdir: Optional parameter for working directory
        :param dict metadata: Optional dictionary used to set up metadata (can be also set by setMetadata() )
        :param bool validateMetaData: Defines if the metadata validation will be called
        """
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=False, **kwargs)

        self._allocateAllModels()
        self._initializeAllModels()

        self.generateModelDependencies()

        if validateMetaData:
            self.validateMetadata(WorkflowMeta)

    def solve(self, runInBackground=False):
        """
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, default False. If True, the solution will run in background (in separate thread or remotely).

        """
        self.setMetadata('Status', 'Running')
        self.setMetadata('Progress', 0.)

        time = 0.*U.s
        timeStepNumber = 0
        while abs(time.inUnitsOf(U.s).getValue()-self._exec_targetTime.inUnitsOf(U.s).getValue()) > 1.e-6:
            time_prev = time
            if self._exec_dt is not None:
                dt = min(self.getCriticalTimeStep(), self._exec_dt)
            else:
                dt = self.getCriticalTimeStep()
            time = time+dt
            if time > self._exec_targetTime:
                time = self._exec_targetTime
                dt = time - time_prev
            timeStepNumber = timeStepNumber+1
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=self._exec_targetTime, number=timeStepNumber)
        
            log.debug("Step %g: t=%g dt=%g" % (timeStepNumber, time.inUnitsOf(U.s).getValue(), dt.inUnitsOf(U.s).getValue()))
            print("Step %g: t=%g dt=%g" % (timeStepNumber, time.inUnitsOf(U.s).getValue(), dt.inUnitsOf(U.s).getValue()))

            # Estimate progress
            self.setMetadata('Progress', 100*time.inUnitsOf(U.s).getValue()/self._exec_targetTime.inUnitsOf(U.s).getValue())
            
            self.solveStep(istep)
            self.finishStep(istep)

        self.setMetadata('Status', 'Finished')
        self.setMetadata('Date_time_end', timeTime.strftime("%Y-%m-%d %H:%M:%S", timeTime.gmtime()))

    def set(self, obj, objectID=""):
        if obj.isInstance(Property):
            if obj.getPropertyID() == DataID.PID_Time:
                if objectID == "targetTime":
                    val = obj.inUnitsOf(U.s).getValue(0.*U.s)
                    if isinstance(val, list) or isinstance(val, tuple) or isinstance(val, numpy.ndarray):
                        self._exec_targetTime = val[0] * U.s  # should not happen anymore
                    else:
                        self._exec_targetTime = val * U.s  # this is correct
                if objectID == "dt":
                    val = obj.inUnitsOf(U.s).getValue()
                    if isinstance(val, list) or isinstance(val, tuple) or isinstance(val, numpy.ndarray):
                        self._exec_dt = val[0] * U.s  # should not happen anymore
                    else:
                        self._exec_dt = val * U.s  # this is correct

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
        # pyroutil.connectNameServer(nshost, nsport, hkey)
        # try:
        #     uri = ns.lookup(workflowMonitorName)
        #     workflowMonitor = Pyro5.api.Proxy(uri)
        # except Exception as e:
        #     log.error("Cannot find workflow monitor")
        #     return # do not raise, silently continue without updating status

        if self.workflowMonitor:
            date = timeTime.strftime("%d %b %Y %H:%M:%S", timeTime.gmtime())
            # metadata = {workflowmonitor.WorkflowMonitorKeys.Status: status,
            # workflowmonitor.WorkflowMonitorKeys.Progress: progress,
            # workflowmonitor.WorkflowMonitorKeys.Date: date}
            metadata = {'WorkflowMonitor.Status': status,
                        'WorkflowMonitor.Progress': progress,
                        'WorkflowMonitor.Date': date}
            
            try:
                self.workflowMonitor.updateMetadata(self.getMetadata('WorkflowMonitor.ComponentID'), metadata)
                # could not use nameserver metadata capability, as this requires workflow to be registered
                # thus Pyro daemon is required

                log.debug(
                    self.getMetadata('WorkflowMonitor.ComponentID') + ": Updated status to " + status + ", progress=" +
                    str(progress)
                )
            except Exception as e:
                log.exception("Connection to workflow monitor broken")
                raise e

    def registerModel(self, mmodel, label=None):
        """
        :param model.Model or model.RemoteModel or Workflow mmodel:
        :param str or None label: Explicit label of the model/workflow, given by the parent workflow.
        """
        if isinstance(mmodel, (Workflow, model.Model, model.RemoteModel, Pyro5.api.Proxy)):
            if label is None:
                i = 0
                while label in self.getListOfModelLabels() or i == 0:
                    i += 1
                    label = "label_%d" % i

            if label not in self.getListOfModelLabels():
                self._models.update({label: mmodel})
            else:
                raise KeyError("Given model label already exists.")
        else:
            raise TypeError("Parameter model should be instance of Workflow, Model, RemoteModel or Pyro5.api.Proxy.")

    def getDictOfModels(self):
        """
        :rtype: dict[model.Model, model.RemoteModel, Workflow]
        """
        return self._models.copy()

    def getListOfModels(self):
        """
        :rtype: list[model.Model, model.RemoteModel, Workflow]
        """
        return iter(self.getDictOfModels().values())

    def getListOfModelLabels(self):
        """
        :rtype: list of str
        """
        return iter(self.getDictOfModels().keys())

    def printListOfModels(self):
        print("List of child models:")
        print([(m.__class__.__name__, m.getApplicationSignature()) for m in self.getListOfModels()])

    def generateModelDependencies(self):
        dependencies = []
        for key_name, _model in self.getDictOfModels().items():
            if isinstance(_model, (model.Model, Workflow, model.RemoteModel)):
                # Temporary fix due to compatibility
                if not _model.hasMetadata('Version_date') and not isinstance(model, Workflow):
                    if _model.hasMetadata('Solver.Version_date'):
                        _model.setMetadata('Version_date', _model.getMetadata('Solver.Version_date'))

                md_name = _model.getMetadata('Name') if _model.hasMetadata('Name') else ''
                md_id = _model.getMetadata('ID') if _model.hasMetadata('ID') else ''
                md_ver = _model.getMetadata('Version_date') if _model.hasMetadata('Version_date') else ''

                m_r_id = {
                    'Label': str(key_name),
                    'Name': md_name,
                    'ID': md_id,
                    'Version_date': md_ver,
                    'Type': 'Workflow' if isinstance(_model, Workflow) else 'Model'
                }
                if isinstance(_model, Workflow):
                    m_r_id.update({'Dependencies': _model.getMetadata('Dependencies')})
                dependencies.append(m_r_id)

        self.setMetadata('Dependencies', dependencies)

    def getExecutionTargetTime(self):
        return self._exec_targetTime

    def getExecutionTimestepLength(self):
        return self._exec_dt

    def getCriticalTimeStep(self):
        if len(self._models):
            return min([m.getCriticalTimeStep() for m in self._models.values()])
        return 1.e10*U.s

    def finishStep(self, tstep):
        for _model in self._models.values():
            try:
                _model.finishStep(tstep)
            except:
                pass

    def terminate(self):
        for _model in self._models.values():
            try:
                _model.terminate()
            except:
                pass
        super().terminate()

    def updateAndPassMetadata(self, dictionary: dict):
        self.updateMetadata(dictionary=dictionary)
        for _model in self._models.values():
            _model.updateAndPassMetadata(dictionary=dictionary)

    @staticmethod
    def checkModelRemoteResource(jobmanagername):
        try:
            ns = pyroutil.connectNameserver()
            jobman = pyroutil.connectJobManager(ns, jobmanagername)
            free_jobs = jobman.getNumberOfFreeJobs()
            if free_jobs:
                log.info("Jobmanager " + jobmanagername + " has " + str(free_jobs) + " free jobs")
                return True
            else:
                log.warning("No available job slots for jobmanager " + jobmanagername)
                return False
        except Exception as e:
            log.exception(e)
            return False

    @staticmethod
    def checkModelRemoteResourcesByMetadata(models_md):
        for model_info in models_md:
            if model_info.get('Jobmanager', ''):
                if Workflow.checkModelRemoteResource(jobmanagername=model_info.get('Jobmanager', '')) is False:
                    return False
        return True
