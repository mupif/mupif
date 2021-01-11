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
import logging
from . import mupifobject
log = logging.getLogger()
import Pyro4

# WM_METADATA_STATUS='status'
# WM_METADATA_PROGRESS='progress'

# class WorkflowMonitorKeys(object):
#     Status = "status"
#     Progress = "progress"
#     Date = "date"
    
# class WorkflowMonitorStatus(object):
#    Initialized="Initialized"
#    Running="Running"
#    Finished="Finished"
#    Failed="Failed"


@Pyro4.expose
class WorkflowMonitor(mupifobject.MupifObject):
    """
    An class implementing workflow monitor; a server keeping track of individual workflow executions and their status.
    It internally maintains workflows dict, where keys are workflow execution IDs, 
    and values are dicts containing metadata.

    .. automethod:: __init__
    """
    def __init__(self):
        """
        Constructor. Initializes the monitor server
        """
        super(WorkflowMonitor, self).__init__()
        # self.workflows={}

    def updateMetadata(self, key, valueDict):
        """
        Updates the entry.
        :param str key: unique execution ID of workflow, application, etc.
        :param dict valueDict: metadata
        """
        if isinstance(valueDict, dict):
            self.metadata.setdefault(key, {}).update(valueDict)

    def getAllMetadata(self):
        """
        Returns all metadata
        :return dict: all metadata
        """
        return self.metadata

