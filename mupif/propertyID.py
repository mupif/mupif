"""
Module defining PropertyID as enumeration, e.g. concentration, velocity.
class Enum allows accessing members by .name and .value
"""

from enum import Enum

class PropertyID(Enum):
    """
    Enumeration class  defining Property IDs. These are used to uniquely determine 
    the canonical keywords identifiing individual properties.
    """
    PID_Concentration = 1
    PID_CumulativeConcentration = 2
    PID_Velocity = 3
    PID_transient_simulation_time = 4
    PID_effective_conductivity = 5
    PID_volume_fraction_red_phosphor = 6
    PID_volume_fraction_green_phosphor = 7
    PID_conductivity_red_phosphor = 8
    PID_conductivity_green_phosphor = 9
    PID_mean_radius_red_phosphor = 10
    PID_mean_radius_green_phosphor = 11
    PID_standard_deviation_red_phosphor = 12
    PID_standard_deviation_green_phosphor = 13


    PID_Demo_Min = 9990
    PID_Demo_Max = 9991
    PID_Demo_Integral = 9992
    PID_Demo_Volume = 9993
    PID_Demo_Value = 9994
