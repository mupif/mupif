"""
Module defining DataID as enumeration, e.g. concentration, velocity.
class Enum allows accessing members by .name and .value
FunctionID is deprecated and will be removed
"""
from enum import IntEnum, auto

# Schema for metadata
DataSchema = {
    "type": "object",
    "properties": {
        "Type": {"type": "string"},  # Automatically generated from MuPIF, e.g. mupif.field.Field
        "Type_ID": {"type": "string"},  # Automatically generated from MuPIF, e.g. DataID.FID_Temperature
        "Name": {"type": "string"},  # e.g. "Density of inclusion"
        "ID": {"type": ["string", "integer"]},  # Unique ID
        "Description": {"type": "string"},  # Further description
        "Units": {"type": "string"},  # Automatically generated from MuPIF, e.g. "kg"
        "ValueType": {"type": "string"},  # Automatically generated
        "Origin": {"type": "string", "enum": ["Experiment", "User_input", "Simulated"]},
        "Experimental_details": {"type": "string"},
        "Experimental_record": {"type": "string"},  # If applies, link to corresponding experimental record
        "Estimated_std": {"type": "number"},  # Percent of standard deviation
        "Execution": {
            "properties": {
                "ID": {"type": ["string", "integer"]},  # Optional execution ID
                "Use_case_ID": {"type": ["string", "integer"]},  # If Simulated, give reference to Use_case_ID
                "Task_ID": {"type": "string"}  # If Simulated, give reference to Task_ID
            },
            "required": []
        }
    },
    "required": [
        "Type", "Type_ID", "Units", "ValueType"
    ]
}


class DataID(IntEnum):
    """
    This class represents the supported values of IDs of property, field, etc.
    Values of members should be stored by .name, .value should not be used.
    """

    # # # # # # # # # # # # # # # # # # # # #

    # Field

    FID_Displacement = auto()
    FID_Strain = auto()
    FID_Stress = auto()
    FID_Temperature = auto()
    FID_Humidity = auto()
    FID_Concentration = auto()
    FID_Thermal_absorption_volume = auto()
    FID_Thermal_absorption_surface = auto()
    FID_Material_number = auto()
    FID_BucklingShape = auto()
    FID_FibreOrientation = auto()
    FID_DomainNumber = auto()
    FID_Permeability = auto()
    FID_Velocity = auto()
    FID_Pressure = auto()
    FID_ESI_VPS_Displacement = auto()
    FID_Porosity = auto()

    # # # # # # # # # # # # # # # # # # # # #

    # GY field IDs

    FID_Mises_Stress = auto()
    FID_MaxPrincipal_Stress = auto()
    FID_MidPrincipal_Stress = auto()
    FID_MinPrincipal_Stress = auto()

    FID_MaxPrincipal_Strain = auto()
    FID_MidPrincipal_Strain = auto()
    FID_MinPrincipal_Strain = auto()

    # # # # # # # # # # # # # # # # # # # # #

    # Particle

    PSID_ParticlePositions = auto()

    # # # # # # # # # # # # # # # # # # # # #

    # Function

    FuncID_ProbabilityDistribution = auto()

    # # # # # # # # # # # # # # # # # # # # #

    # Misc

    ID_None = auto()
    ID_GrainState = auto()
    ID_MoleculeState = auto()
    ID_InputFile = auto()
    ID_ForceField = auto()

    # # # # # # # # # # # # # # # # # # # # #

    # Property

    PID_Concentration = auto()
    PID_CumulativeConcentration = auto()
    PID_Velocity = auto()
    PID_transient_simulation_time = auto()
    PID_effective_conductivity = auto()
    PID_volume_fraction_red_phosphor = auto()
    PID_volume_fraction_green_phosphor = auto()
    PID_conductivity_red_phosphor = auto()
    PID_conductivity_green_phosphor = auto()
    PID_mean_radius_red_phosphor = auto()
    PID_mean_radius_green_phosphor = auto()
    PID_standard_deviation_red_phosphor = auto()
    PID_standard_deviation_green_phosphor = auto()
    PID_RefractiveIndex = auto()
    PID_NumberOfRays = auto()
    PID_LEDSpectrum = auto()
    PID_ChipSpectrum = auto()
    PID_LEDColor_x = auto()
    PID_LEDColor_y = auto()
    PID_LEDCCT = auto()
    PID_LEDRadiantPower = auto()
    PID_ParticleNumberDensity = auto()
    PID_ParticleRefractiveIndex = auto()
    PID_EmissionSpectrum = auto()
    PID_ExcitationSpectrum = auto()
    PID_AsorptionSpectrum = auto()
    PID_ScatteringCrossSections = auto()
    PID_InverseCumulativeDist = auto()
    PID_NumberOfFluorescentParticles = auto()
    PID_ParticleMu = auto()
    PID_ParticleSigma = auto()
    PID_PhosphorEfficiency = auto()
    PID_Length = auto()
    PID_Height = auto()
    PID_Thickness = auto()
    PID_Deflection = auto()
    PID_EModulus = auto()  # Young's modulus
    PID_PoissonRatio = auto()
    # Mul2 properties
    PID_YoungModulus1 = auto()
    PID_YoungModulus2 = auto()
    PID_YoungModulus3 = auto()
    PID_PoissonRatio23 = auto()
    PID_PoissonRatio13 = auto()
    PID_PoissonRatio12 = auto()
    PID_ShearModulus23 = auto()
    PID_ShearModulus13 = auto()
    PID_ShearModulus12 = auto()
    PID_CriticalLoadLevel = auto()
    # INSA properties
    PID_ExtensionalInPlaneStiffness = auto()
    PID_ExtensionalOutOfPlaneStiffness = auto()
    PID_ShearInPlaneStiffness = auto()
    PID_ShearOutOfPlaneStiffness = auto()
    PID_LocalBendingStiffness = auto()
    PID_CriticalForce = auto()
    PID_CriticalMoment = auto()
    # Digimat Properties
    PID_MatrixYoung = auto()
    PID_MatrixPoisson = auto()
    PID_InclusionYoung = auto()
    PID_InclusionPoisson = auto()
    PID_InclusionVolumeFraction = auto()
    PID_InclusionAspectRatio = auto()
    PID_MatrixOgdenModulus = auto()
    PID_MatrixOgdenExponent = auto()
    PID_InclusionSizeNormalized = auto()

    PID_CompositeAxialYoung = auto()
    PID_CompositeInPlaneYoung = auto()
    PID_CompositeInPlaneShear = auto()
    PID_CompositeTransverseShear = auto()
    PID_CompositeInPlanePoisson = auto()
    PID_CompositeTransversePoisson = auto()
    PID_CompositeStrain11Tensor = auto()
    PID_CompositeStrain22Tensor = auto()
    PID_CompositeStress11Tensor = auto()
    PID_MatrixDensity = auto()
    PID_CompositeDensity = auto()
    PID_InclusionDensity = auto()

    # CUBA keywords from Jun 6, 2017 - https://github.com/simphony/simphony-common/blob/master/ontology/cuba.yml
    PID_Position = auto()
    PID_Direction = auto()
    PID_Status = auto()
    PID_Label = auto()
    PID_Chemical_specie = auto()
    PID_Material_type = auto()
    PID_Shape_center = auto()
    PID_Shape_length = auto()
    PID_Shape_radius = auto()
    PID_Shape_side = auto()
    PID_Crystal_storage = auto()
    PID_Name_UC = auto()
    PID_Lattice_vectors = auto()
    PID_Symmetry_lattice_vectors = auto()
    PID_Occupancy = auto()
    PID_Bond_label = auto()
    PID_Bond_type = auto()
    # PID_Velocity = auto() Duplicate
    PID_Dimension = auto()
    PID_Acceleration = auto()
    PID_Radius = auto()
    PID_Size = auto()
    PID_Mass = auto()
    PID_Volume = auto()
    PID_Angular_velocity = auto()
    PID_Angular_acceleration = auto()
    PID_Simulation_domain_dimensions = auto()
    PID_Simulation_domain_origin = auto()
    PID_Dynamic_viscosity = auto()
    PID_Kinematic_viscosity = auto()
    PID_Diffusion_coefficient = auto()
    PID_Probability_coefficient = auto()
    PID_Friction_coefficient = auto()
    PID_Scaling_coefficient = auto()
    PID_Equation_of_state_coefficient = auto()
    PID_Contact_angle = auto()
    PID_Amphiphilicity = auto()
    PID_Phase_interaction_strength = auto()
    PID_Hamaker_constant = auto()
    PID_Zeta_potential = auto()
    PID_Ion_valence_effect = auto()
    PID_Debye_length = auto()
    PID_Smoothing_length = auto()
    PID_Lattice_spacing = auto()
    PID_Time_step = auto()
    PID_Number_of_time_steps = auto()
    PID_Force = auto()
    PID_Torque = auto()
    PID_Density = auto()
    PID_Pressure = auto()
    PID_Temperature = auto()
    PID_Distribution = auto()
    PID_Order_parameter = auto()
    PID_Original_position = auto()
    PID_Current = auto()
    PID_Final = auto()
    PID_Delta_displacement = auto()
    PID_External_applied_force = auto()
    PID_Euler_angles = auto()
    PID_Sphericity = auto()
    PID_Young_modulus = auto()
    PID_Poisson_ratio = auto()
    PID_Restitution_coefficient = auto()
    PID_Rolling_friction = auto()
    PID_Volume_fraction = auto()
    PID_Coupling_time = auto()
    PID_Cutoff_distance = auto()
    PID_Energy_well_depth = auto()
    PID_Van_der_Waals_radius = auto()
    PID_Dielectric_constant = auto()
    PID_Dynamic_pressure = auto()
    PID_Flux = auto()
    PID_Homogenized_stress_tensor = auto()
    PID_Strain_tensor = auto()
    PID_Relative_velocity = auto()
    PID_Diffusion_velocity = auto()
    PID_Stress_tensor = auto()
    PID_Volume_fraction_gradient = auto()
    PID_Cohesion_energy_density = auto()
    PID_Major = auto()
    PID_Minor = auto()
    PID_Patch = auto()
    PID_Full = auto()
    PID_Charge = auto()
    PID_Charge_density = auto()
    PID_Description = auto()
    PID_Electric_field = auto()
    PID_Electron_mass = auto()
    PID_Electrostatic_field = auto()
    PID_Energy = auto()
    PID_Heat_conductivity = auto()
    PID_Initial_viscosity = auto()
    PID_Linear_constant = auto()
    PID_Maximum_viscosity = auto()
    PID_Minimum_viscosity = auto()
    PID_Momentum = auto()
    PID_Moment_inertia = auto()
    PID_Potential_energy = auto()
    PID_Power_law_index = auto()
    PID_Relaxation_time = auto()
    PID_Surface_tension = auto()
    PID_Time = auto()
    PID_Viscosity = auto()
    PID_Collision_operator = auto()
    PID_Reference_density = auto()
    PID_External_forcing = auto()
    PID_Flow_type = auto()
    PID_Vector = auto()
    PID_Index = auto()
    PID_Thermodynamic_ensemble = auto()
    PID_Variable = auto()
    PID_None = auto()
    PID_Lattice_parameter = auto()
    PID_Steady_state = auto()
    PID_Maximum_Courant_number = auto()
    PID_Number_of_cores = auto()
    PID_Magnitude = auto()
    PID_Number_of_physics_states = auto()
    PID_Cohesive_group = auto()
    PID_FillingTime = auto()
    # End of CUBA keywords

    PID_Demo_Min = auto()
    PID_Demo_Max = auto()
    PID_Demo_Integral = auto()
    PID_Demo_Volume = auto()
    PID_Demo_Value = auto()
    PID_UserTimeStep = auto()
    PID_KPI01 = auto()

    # ESI VPS properties
    PID_ESI_VPS_TEND = auto()
    PID_ESI_VPS_PLY1_E0t1 = auto()
    PID_ESI_VPS_PLY1_E0t2 = auto()
    PID_ESI_VPS_PLY1_E0t3 = auto()
    PID_ESI_VPS_PLY1_G012 = auto()
    PID_ESI_VPS_PLY1_G023 = auto()
    PID_ESI_VPS_PLY1_G013 = auto()
    PID_ESI_VPS_PLY1_NU12 = auto()
    PID_ESI_VPS_PLY1_NU23 = auto()
    PID_ESI_VPS_PLY1_NU13 = auto()
    PID_ESI_VPS_PLY1_E0c1 = auto()
    PID_ESI_VPS_PLY1_RHO = auto()
    PID_ESI_VPS_hPLY = auto()
    PID_ESI_VPS_PLY1_XT = auto()
    PID_ESI_VPS_PLY1_XC = auto()
    PID_ESI_VPS_PLY1_YT = auto()
    PID_ESI_VPS_PLY1_YC = auto()
    PID_ESI_VPS_PLY1_S12 = auto()

    PID_ESI_VPS_FIRST_FAILURE_VAL = auto()
    PID_ESI_VPS_FIRST_FAILURE_MOM = auto()
    PID_ESI_VPS_FIRST_FAILURE_ROT = auto()
    PID_ESI_VPS_CRIMP_STIFFNESS = auto()
    PID_ESI_VPS_FIRST_FAILURE_ELE = auto()
    PID_ESI_VPS_FIRST_FAILURE_PLY = auto()
    PID_ESI_VPS_TOTAL_MODEL_MASS = auto()
    PID_ESI_VPS_BUCKL_LOAD = auto()
    PID_ESI_VPS_MOMENT_CURVE = auto()
    PID_ESI_VPS_ROTATION_CURVE = auto()

    PID_ESI_VPS_MOMENT = auto()
    PID_ESI_VPS_ROTATION = auto()
    PID_ESI_VPS_THNOD_1 = auto()
    PID_ESI_VPS_THNOD_2 = auto()
    PID_ESI_VPS_SECFO_1 = auto()
    PID_ESI_VPS_SECFO_2 = auto()

    PID_BoundaryConfiguration = auto()

    # University of Trieste properties
    PID_SMILE_MOLECULAR_STRUCTURE = auto()
    PID_MOLECULAR_WEIGHT = auto()
    PID_POLYDISPERSITY_INDEX = auto()
    PID_CROSSLINKER_TYPE = auto()
    PID_FILLER_DESIGNATION = auto()
    PID_SMILE_MODIFIER_MOLECULAR_STRUCTURE = auto()
    PID_SMILE_FILLER_MOLECULAR_STRUCTURE = auto()
    PID_CROSSLINKONG_DENSITY = auto()
    PID_FILLER_CONCENTRATION = auto()
    PID_DENSITY_OF_FUNCTIONALIZATION = auto()
    PID_TEMPERATURE = auto()
    PID_PRESSURE = auto()
    PID_DENSITY = auto()
    PID_TRANSITION_TEMPERATURE = auto()
    # GY user-case property IDs
    PID_HyperelasticPotential = auto()
    PID_ForceCurve = auto()
    PID_DisplacementCurve = auto()
    PID_CorneringAngle = auto()
    PID_CorneringStiffness = auto()

    # Demo properties
    PID_dirichletBC = auto()
    PID_conventionExternalTemperature = auto()
    PID_conventionCoefficient = auto()
    # GY property IDs
    PID_Footprint = auto()
    PID_Braking_Force = auto()
    PID_Stiffness = auto()
    PID_Hyper1 = auto()
    PID_maxDisplacement = auto()
    PID_maxMisesStress = auto()
    PID_maxPrincipalStress = auto()
    PID_Hyper2 = auto()

    #
    PID_NrOfComponents = auto()
    PID_Self_Diffusivity = auto()
    PID_Mass_density = auto()
    PID_Interface_width = auto()
    PID_Degree_of_polymerization = auto()
    PID_Interaction_parameter = auto()
    PID_Molar_volume = auto()

    #
    PID_GrainState = auto()

    #
    PID_HOMO = auto()
    PID_LUMO = auto()

    #

    PID_InletVelocity = auto()
    PID_OutletVelocity = auto()
    PID_BeltVelocity = auto()
    PID_InletTemperature = auto()
    PID_BeltTemperature = auto()
    PID_EnvTemperature = auto()
    PID_SolverTimeSteps = auto()
    PID_SolverStartFilm = auto()
    PID_SolverOutputStep = auto()
    PID_TinflowSolvent = auto()
    PID_TinflowBackground = auto()
    PID_TinflowModelID = auto()
    PID_TinflowModelConfig = auto()
    PID_FilmThickness = auto()
    PID_FlagNewModel = auto()
    PID_FlagRestart = auto()
    PID_FlagPostProcess = auto()
    PID_FlagVerbose = auto()
    PID_TinflowInputFile = auto()
    FID_FilmThickness = auto()
    FID_FilmEvaporationRate = auto()
    FID_FilmTemperature = auto()
    FID_FilmConcentration = auto()
    PID_HeaterTemperature = auto()
    PID_SolverDeltaT = auto()
    PID_FilmTemperature = auto()
    PID_TinflowProp1 = auto()
    PID_TinflowProp2 = auto()
    PID_TinflowProp3 = auto()
