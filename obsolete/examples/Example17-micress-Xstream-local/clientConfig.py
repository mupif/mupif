#
#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#  CIGS example: configuration 
#
#  Copyright (C) 2014-2016 
#  Ralph Altenfeld, Access, Intzestr.5, Aachen, Germany
#  
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
This configuration file provides necessary information for the
top-level scenario script, i.e. CIGS_example.py:

- local working directory
- input files for individual applications
- number of used interfaces
- debug message settings
- simulation time
- start emissivity for X-Stream
- interpolation surface mesh settings
- monitor files

See source code comments for more information.

"""

import sys
sys.path.append('../../..') # Mupif path

# the working directory will contains some pre-calculated results
# from X-Stream and MICRESS for this example
if ( sys.platform.lower().startswith('lin') ):
  localWorkdir = "./workbench"
else:
  localWorkdir = ".\workbench"

# input subdirectories relativ to working directory of the top-level script, i.e.
# file location of Precursor_B.txt is "./in_qFact/Precursor_B.txt"
micressPrefix = 'in_micress'
xstreamPrefix = 'in_xstream'
qfactPrefix = 'in_qFact'
#micressInputFiles = ('mob_CIGS_exp.txt','mob_gas_exp.txt','mob_others_exp.txt','RVE5_3Phases_mobT_B_T2a.template')
micressInputFiles = ('mob_CIGS_calibrated.txt','mob_gas_exp.txt','RVE5_3Phases_mobT_B_T2a.template')
xstreamInputFiles = ('input.in','MMPTESTCASE.grd','MMPTestCase_v2_transient.cas')
qFactInputFiles = ('Precursor_B.txt','ReducedQfactors.txt')

# number of application interfaces
# In this example, these numbers have to match to the setting used for pre-calculating data.
# Just to find the data.
xstreamJobs = 1
micressJobs = 2

# debug output settings
debug = False  # while running the test case itself
debugComm = False  # while setting up the communication environment (SSH tunnels, job allocation, etc.)
mupifLogging = False  # screen output for Mupif internal logging (e.g. from pyroutil )

startTime = 0.0 # simulation's start time in seconds
targetTime = 2.0 # simulations's target time in seconds

startEmissivity = 0.55 # X-Stream start boundary condition for emissivity                 

# mesh definition of the 2D plane of glass substrate's surface
# The nodes of this mesh will be serve as RVE locations on a microstructural level
nbX = 3 # number of nodes
nbY = 3
nbZ = 0
lenX = 0.03 # length in meter
lenY = 0.03
lenZ = 0
originX = -0.015 # origin at the corner, coordinates in meter
originY = -0.015
originZ = 0.0 # current Z coordinate for glas substrate surface

# monitor files
monFilenames = ("Temperature_Profile.txt", \
                "SE_Concentration_Profile.txt", \
                "Average_Grain_Size_Profile.txt", \
                "CIGS_Layer_Thickness_Profile.txt", \
                "Fraction_Cu_2-x_Se_Profile.txt", \
                "Fraction_Cu_In_Ga_3Se5_Profile.txt", \
                "Quality_Factor.txt", \
                "Emissivity_Contribution.txt", \
                "Fraction_CIGS_Profile.txt")

