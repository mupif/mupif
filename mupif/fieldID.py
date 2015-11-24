""" 
This class represent the supported values of field IDs, e.g. displacement, strain, temperature.
class Enum allows accessing members by .name and .value
"""

from enum import Enum

class FieldID(Enum):
    FID_Displacement = 1
    FID_Strain = 2
    FID_Stress = 3
    FID_Temperature = 4
    FID_Humidity = 5
    FID_Concentration = 6
    FID_Thermal_absorption_volume = 7
    FID_Thermal_absorption_surface = 8
