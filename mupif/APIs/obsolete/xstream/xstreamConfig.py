#
#
#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#  Copyright (C) 2014-2016
#  Luuk Thielen (CelSian Glass&Solar, The Netherlands)
# 
# This script code is free software; you can redistribute it and/or
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
#

""" 
  X-Stream interface configuration file

  This file provides necessary information about the X-Stream installation
  which should be steered by the interface.

  :note: In this example, X-Stream will not be run directly. All result data is pre-calculated
  
"""

# local
xstreamPath = ".../X-stream_Bin/"
xstreamExec = "GTM-X_V4_6MMP_Version.LINUX"
xstreamLicenseServer = "..."
nbOfProcesses = 6  # modify machine file manually
mpirun = ".../mpich-1.2.7/bin/mpirun"
machinefile = xstreamPath + 'nodefile'

# default sub folders
ensightPath = "./ensight"
copyFolder = "backup"

DebugMode = False
BackUpFiles = False
