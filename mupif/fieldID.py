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

from enum import Enum

class FieldID(Enum):
    """ 
    This class represent the supported values of field IDs, e.g. displacement, strain, temperature.
    Immutable class Enum allows accessing members by .name and .value methods
    """
    FID_Displacement = 1
    FID_Strain = 2
    FID_Stress = 3
    FID_Temperature = 4
    FID_Humidity = 5
    FID_Concentration = 6
    FID_Thermal_absorption_volume = 7
    FID_Thermal_absorption_surface = 8
