"""
Module defining PropertyID as enumeration, e.g. concentration, velocity.
class Enum allows accessing members by .name and .value
"""
#needs a module enum34
from enum import IntEnum

class PropertyID(IntEnum):
    """
    Enumeration class defining Property IDs. These are used to uniquely determine 
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
    PID_RefractiveIndex = 14
    PID_NumberOfRays = 15
    PID_LEDSpectrum = 16
    PID_ChipSpectrum = 17
    PID_LEDColor_x = 18
    PID_LEDColor_y = 19
    PID_LEDCCT = 20
    PID_LEDRadiantPower = 21
    PID_ParticleNumberDensity = 22
    PID_ParticleRefractiveIndex = 23
    PID_EmissionSpectrum = 24
    PID_ExcitationSpectrum = 25
    PID_AsorptionSpectrum = 26
    PID_ScatteringCrossSections = 27
    PID_InverseCumulativeDist = 28
    PID_NumberOfFluorescentParticles = 29
    PID_ParticleMu = 30
    PID_ParticleSigma = 31
    PID_PhosphorEfficiency = 32
    PID_Length = 33
    PID_Height = 34
    PID_Thickness = 35
    PID_Deflection = 36
    PID_EModulus = 37 #Young's modulus
    

    PID_Demo_Min = 9990
    PID_Demo_Max = 9991
    PID_Demo_Integral = 9992
    PID_Demo_Volume = 9993
    PID_Demo_Value = 9994
    PID_UserTimeStep = 9995
    PID_KPI01 = 9996

    # ESI VPS properties
    PID_ESI_VPS_TEND      = 90001
    
    PID_ESI_VPS_PLY1_E0t1 = 90002
    PID_ESI_VPS_PLY1_E0t2 = 90003
    PID_ESI_VPS_PLY1_E0t3 = 90004
    PID_ESI_VPS_PLY1_G012 = 90005
    PID_ESI_VPS_PLY1_G023 = 90006
    PID_ESI_VPS_PLY1_G013 = 90007
    PID_ESI_VPS_PLY1_NU12 = 90008
    PID_ESI_VPS_PLY1_NU23 = 90009
    PID_ESI_VPS_PLY1_NU13 = 90010
    PID_ESI_VPS_PLY1_E0c1 = 90011
    
    PID_ESI_VPS_PLY1_RHO  = 90012
    
    PID_ESI_VPS_hPLY      = 90013
    
    PID_ESI_VPS_PLY1_XT   = 90014
    PID_ESI_VPS_PLY1_XC   = 90015
    PID_ESI_VPS_PLY1_YT   = 90016
    PID_ESI_VPS_PLY1_YC   = 90017
    PID_ESI_VPS_PLY1_S12  = 90018
    
    PID_ESI_VPS_THNOD_1   = 91001
    PID_ESI_VPS_THNOD_2   = 91002
    PID_ESI_VPS_SECFO_1   = 91003
    PID_ESI_VPS_SECFO_2   = 91004
