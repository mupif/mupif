"""
Module defining PropertyID and FieldID as enumeration, e.g. concentration, velocity.
class Enum allows accessing members by .name and .value
FunctionID is deprecated and will be removed
"""
from enum import IntEnum

# Schema for metadata
DataSchema = {
    'type': 'object',
    'properties': {
        'Type': {'type': 'string'},  # Automatically generated from MuPIF, e.g. mupif.Field.Field
        'Type_ID': {'type': 'string'},  # Automatically generated from MuPIF, e.g. FieldID.FID_Temperature
        'Name': {'type': 'string'},  # e.g. 'Density of inclusion'
        'ID': {'type': ['string', 'integer']},  # Unique ID
        'Description': {'type': 'string'},  # Further description
        'Units': {'type': 'string'},  # Automatically generated from MuPIF, e.g. 'kg'
        'ValueType': {'type': 'string'},  # Automatically generated
        'Origin': {'type': 'string', 'enum': ['Experiment', 'User_input', 'Simulated']},
        'Experimental_details': {'type': 'string'},
        'Experimental_record': {'type': 'string'},  # If applies, link to corresponding experimental record
        'Estimated_std': {'type': 'number'},  # Percent of standard deviation
        'Execution': {
            'properties': {
                'ID': {'type': ['string', 'integer']},  # Optional execution ID
                'Use_case_ID': {'type': ['string', 'integer']},  # If Simulated, give reference to Use_case_ID
                'Task_ID': {'type': 'string'}  # If Simulated, give reference to Task_ID
            },
            'required': []
        }
    },
    'required': [
        'Type', 'Type_ID', 'Units', 'ValueType'
    ]
}


class FieldID(IntEnum):
    """
    This class represents the supported values of field IDs, e.g. displacement, strain, temperature.
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
    FID_Material_number = 9
    FID_BucklingShape = 10
    FID_FibreOrientation = 11
    FID_DomainNumber = 12
    FID_Permeability = 13
    FID_ESI_VPS_Displacement = 10001

    # GY field IDs
    FID_Mises_Stress = 2000000
    FID_MaxPrincipal_Stress = 2000001
    FID_MidPrincipal_Stress = 2000002
    FID_MinPrincipal_Stress = 2000003
    
    FID_MaxPrincipal_Strain = 2000004
    FID_MidPrincipal_Strain = 2000005
    FID_MinPrincipal_Strain = 2000006

class ParticleSetID(IntEnum):
    """
    This class represents supported values of ParticleSetID, an unique ID identifier for ParticleSet type.
    """
    PSID_ParticlePositions = 1

class FunctionID(IntEnum):
    """
    This classenumeration represent the supported values of FunctionID, e.g. FuncID_ProbabilityDistribution
    """
    FuncID_ProbabilityDistribution = 1


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
    PID_EModulus = 37  # Young's modulus
    PID_PoissonRatio = 38
    # Mul2 properties
    PID_YoungModulus1 = 39
    PID_YoungModulus2 = 40
    PID_YoungModulus3 = 41
    PID_PoissonRatio23 = 42
    PID_PoissonRatio13 = 43
    PID_PoissonRatio12 = 44
    PID_ShearModulus23 = 45
    PID_ShearModulus13 = 46
    PID_ShearModulus12 = 47
    PID_CriticalLoadLevel = 48
    # INSA properties
    PID_ExtensionalInPlaneStiffness = 49
    PID_ExtensionalOutOfPlaneStiffness = 50
    PID_ShearInPlaneStiffness = 51
    PID_ShearOutOfPlaneStiffness = 52
    PID_LocalBendingStiffness = 53
    PID_CriticalForce  = 54
    PID_CriticalMoment = 55
    # Digimat Properties
    PID_MatrixYoung = 8000
    PID_MatrixPoisson = 8001
    PID_InclusionYoung = 8002
    PID_InclusionPoisson = 8003
    PID_InclusionVolumeFraction = 8004
    PID_InclusionAspectRatio = 8005
    PID_MatrixOgdenModulus          = 8006
    PID_MatrixOgdenExponent         = 8007
    PID_InclusionSizeNormalized     = 8012
    
    PID_CompositeAxialYoung = 9000
    PID_CompositeInPlaneYoung = 9001
    PID_CompositeInPlaneShear = 9002
    PID_CompositeTransverseShear = 9003
    PID_CompositeInPlanePoisson = 9004
    PID_CompositeTransversePoisson = 9005
    PID_CompositeStrain11Tensor     = 9006
    PID_CompositeStrain22Tensor     = 9007
    PID_CompositeStress11Tensor     = 9008
    PID_MatrixDensity = 8008
    PID_CompositeDensity = 9009
    PID_InclusionDensity = 8009


    # CUBA keywords from Jun 6, 2017 - https://github.com/simphony/simphony-common/blob/master/ontology/cuba.yml
    PID_Position = 1000
    PID_Direction = 1001
    PID_Status = 1002
    PID_Label = 1003
    PID_Chemical_specie = 1004
    PID_Material_type = 1005
    PID_Shape_center = 1006
    PID_Shape_length = 1007
    PID_Shape_radius = 1008
    PID_Shape_side = 1009
    PID_Crystal_storage = 1010
    PID_Name_UC = 1011
    PID_Lattice_vectors = 1012
    PID_Symmetry_lattice_vectors = 1013
    PID_Occupancy = 1014
    PID_Bond_label = 1015
    PID_Bond_type = 1016
    # PID_Velocity = 1017 Duplicate
    PID_Dimension = 1017
    PID_Acceleration = 1018
    PID_Radius = 1019
    PID_Size = 1020
    PID_Mass = 1021
    PID_Volume = 1022
    PID_Angular_velocity = 1023
    PID_Angular_acceleration = 1024
    PID_Simulation_domain_dimensions = 1025
    PID_Simulation_domain_origin = 1026
    PID_Dynamic_viscosity = 1027
    PID_Kinematic_viscosity = 1028
    PID_Diffusion_coefficient = 1029
    PID_Probability_coefficient = 1030
    PID_Friction_coefficient = 1031
    PID_Scaling_coefficient = 1032
    PID_Equation_of_state_coefficient = 1033
    PID_Contact_angle = 1034
    PID_Amphiphilicity = 1035
    PID_Phase_interaction_strength = 1036
    PID_Hamaker_constant = 1037
    PID_Zeta_potential = 1038
    PID_Ion_valence_effect = 1039
    PID_Debye_length = 1040
    PID_Smoothing_length = 1041
    PID_Lattice_spacing = 1042
    PID_Time_step = 1043
    PID_Number_of_time_steps = 1044
    PID_Force = 1045
    PID_Torque = 1046
    PID_Density = 1047
    # PID_Concentration = 1048 Duplicity
    PID_Pressure = 1049
    PID_Temperature = 1050
    PID_Distribution = 1051
    PID_Order_parameter = 1052
    PID_Original_position = 1053
    PID_Current = 1054
    PID_Final = 1055
    PID_Delta_displacement = 1056
    PID_External_applied_force = 1057
    PID_Euler_angles = 1058
    PID_Sphericity = 1059
    PID_Young_modulus = 1060
    PID_Poisson_ratio = 1061
    PID_Restitution_coefficient = 1062
    PID_Rolling_friction = 1063
    PID_Volume_fraction = 1064
    PID_Coupling_time = 1065
    PID_Cutoff_distance = 1066
    PID_Energy_well_depth = 1067
    PID_Van_der_Waals_radius = 1068
    PID_Dielectric_constant = 1069
    PID_Dynamic_pressure = 1070
    PID_Flux = 1071
    PID_Homogenized_stress_tensor = 1072
    PID_Strain_tensor = 1073
    PID_Relative_velocity = 1074
    PID_Diffusion_velocity = 1075
    PID_Stress_tensor = 1076
    PID_Volume_fraction_gradient = 1077
    PID_Cohesion_energy_density = 1078
    PID_Major = 1079
    PID_Minor = 1080
    PID_Patch = 1081
    PID_Full = 1082
    PID_Charge = 1083
    PID_Charge_density = 1084
    PID_Description = 1085
    PID_Electric_field = 1086
    PID_Electron_mass = 1087
    PID_Electrostatic_field = 1088
    PID_Energy = 1089
    PID_Heat_conductivity = 1090
    PID_Initial_viscosity = 1091
    PID_Linear_constant = 1092
    PID_Maximum_viscosity = 1093
    PID_Minimum_viscosity = 1094
    PID_Momentum = 1095
    PID_Moment_inertia = 1096
    PID_Potential_energy = 1097
    PID_Power_law_index = 1098
    PID_Relaxation_time = 1099
    PID_Surface_tension = 1100
    PID_Time = 1101
    PID_Viscosity = 1102
    PID_Collision_operator = 1103
    PID_Reference_density = 1104
    PID_External_forcing = 1105
    PID_Flow_type = 1106
    PID_Vector = 1107
    PID_Index = 1108
    PID_Thermodynamic_ensemble = 1109
    PID_Variable = 1110
    PID_None = 1111
    PID_Lattice_parameter = 1112
    PID_Steady_state = 1113
    PID_Maximum_Courant_number = 1114
    PID_Number_of_cores = 1115
    PID_Magnitude = 1116
    PID_Number_of_physics_states = 1117
    PID_Cohesive_group = 1118
    PID_FillingTime = 1119
    # End of CUBA keywords
    
    PID_Demo_Min = 9990
    PID_Demo_Max = 9991
    PID_Demo_Integral = 9992
    PID_Demo_Volume = 9993
    PID_Demo_Value = 9994
    PID_UserTimeStep = 9995
    PID_KPI01 = 9996

    # ESI VPS properties
    PID_ESI_VPS_TEND = 90001
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
    PID_ESI_VPS_PLY1_RHO = 90012
    PID_ESI_VPS_hPLY = 90013
    PID_ESI_VPS_PLY1_XT = 90014
    PID_ESI_VPS_PLY1_XC = 90015
    PID_ESI_VPS_PLY1_YT = 90016
    PID_ESI_VPS_PLY1_YC = 90017
    PID_ESI_VPS_PLY1_S12 = 90018

    PID_ESI_VPS_FIRST_FAILURE_VAL = 91000
    PID_ESI_VPS_FIRST_FAILURE_MOM = 91001
    PID_ESI_VPS_FIRST_FAILURE_ROT = 91002
    PID_ESI_VPS_CRIMP_STIFFNESS = 91003
    PID_ESI_VPS_FIRST_FAILURE_ELE = 91004
    PID_ESI_VPS_FIRST_FAILURE_PLY = 91005
    PID_ESI_VPS_TOTAL_MODEL_MASS = 91006
    PID_ESI_VPS_BUCKL_LOAD = 91007
    PID_ESI_VPS_MOMENT_CURVE = 91008
    PID_ESI_VPS_ROTATION_CURVE = 91009

    PID_ESI_VPS_MOMENT = 90019
    PID_ESI_VPS_ROTATION = 90020
    PID_ESI_VPS_THNOD_1 = 90021
    PID_ESI_VPS_THNOD_2 = 90022
    PID_ESI_VPS_SECFO_1 = 90023
    PID_ESI_VPS_SECFO_2 = 90024
    
    PID_BoundaryConfiguration = 95000

    # University of Trieste properties
    PID_SMILE_MOLECULAR_STRUCTURE = 92000
    PID_MOLECULAR_WEIGHT = 92001
    PID_POLYDISPERSITY_INDEX = 92002
    PID_CROSSLINKER_TYPE = 92003
    PID_FILLER_DESIGNATION = 92004
    PID_SMILE_MODIFIER_MOLECULAR_STRUCTURE = 92005
    PID_SMILE_FILLER_MOLECULAR_STRUCTURE = 92006
    PID_CROSSLINKONG_DENSITY = 92007
    PID_FILLER_CONCENTRATION = 92008
    PID_DENSITY_OF_FUNCTIONALIZATION = 92009
    PID_TEMPERATURE = 92010
    PID_PRESSURE = 92011
    PID_DENSITY = 92100
    PID_TRANSITION_TEMPERATURE = 92101
    # GY user-case property IDs
    PID_HyperelasticPotential = 92200
    PID_ForceCurve`= 92201
    PID_DisplacementCurve= 92202
    PID_CorneringAngle= 92203
    PID_CorneringStiffness= 92204
    

    # Demo properties
    PID_dirichletBC = 97000
    PID_conventionExternalTemperature = 97001
    PID_conventionCoefficient = 97002
    # GY property IDs
    PID_Footprint = 1000000
    PID_Braking_Force = 1000001
    PID_Stiffness = 1000002
    PID_Hyper1 = 1000003
    PID_maxDisplacement = 1000004
    PID_maxMisesStress = 1000005
    PID_maxPrincipalStress = 1000006
    PID_Hyper2 = 1000007
