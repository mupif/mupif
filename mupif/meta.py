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


import pydantic
from pydantic import Field
from typing import Optional, Any, Literal, Union, List
from .dataid import DataID

prefix = "mupif."
type_ids = []
type_ids.extend(prefix+s for s in list(map(str, DataID)))


class PhysicsMeta(pydantic.BaseModel):
    Type: Literal['Electronic', 'Atomistic', 'Molecular', 'Mesoscopic', 'Continuum', 'Other']
    Entity: Literal['Atom', 'Electron', 'Grains', 'Finite volume', 'Other']
    Entity_description: str = ''
    Equation: List[str] = []
    Equation_quantities: List[str] = []
    Relation_description: List[str] = []


class SolverMeta(pydantic.BaseModel):
    Software: str
    Language: str
    License: str
    Creator: str
    Version_date: str
    Solver_additional_params: str = ''
    Documentation: str
    Estim_time_step_s: float
    Estim_comp_time_s: float
    Estim_execution_cost_EUR: float
    Estim_personnel_cost_EUR: float
    Required_expertise:  Literal["None", "User", "Expert"]
    Accuracy:  Literal["Low", "Medium", "High", "Unknown"]
    Sensitivity:  Literal["Low", "Medium", "High", "Unknown"]
    Complexity:  Literal["Low", "Medium", "High", "Unknown"]
    Robustness:  Literal["Low", "Medium", "High", "Unknown"]


# See https://docs.pydantic.dev/1.10/usage/schema/ for possible Field(...) arguments
# the first positional argument is the default value, doc translates to JSON Schema description field
class ExecutionMeta(pydantic.BaseModel):
    '''Execution metadata, for use by the MuPIF infrastructure.'''
    ID: str = ''
    Use_case_ID: Union[str, int] = ''
    Task_ID: str = ''
    Log_URI: str = Field('',description='Internal use only: Pyro URI of the remote logger object, valid only when the workflow is running.')
    Status: Literal["Instantiated", "Initialized", "Running", "Finished", "Failed"] = Field(default='Instantiated',description='Set by the workflow scheduler automatically')
    Progress: float = Field(-1,description='Floating progress in range 0…1; may be set by the workflow, but is not mandatory. Ignored if negative.')
    Date_time_start: str = Field('',description='Automatically set in Workflow')
    Date_time_end: str = Field('',description='Automatically set in Workflow')
    Timeout: int = Field(0,description='Maximum runtime in seconds; unlimited if non-positive')
    Username: str = Field('',description='Automatically set in Model and Workflow')
    Hostname: str = Field('',description='Automatically set in Model and Workflow')
    ExecutionProfileIndex: int = -1


class IOMeta(pydantic.BaseModel):
    Type: Literal[
        'mupif.Property',
        'mupif.TemporalProperty',
        'mupif.Field',
        'mupif.TemporalField',
        'mupif.HeavyStruct',
        'mupif.PyroFile',
        'mupif.String',
        'mupif.ParticleSet',
        'mupif.GrainState',
        'mupif.Function',
        'mupif.DataList[mupif.Property]',
        'mupif.DataList[mupif.TemporalProperty]',
        'mupif.DataList[mupif.Field]',
        'mupif.DataList[mupif.TemporalField]',
        'mupif.DataList[mupif.HeavyStruct]',
        'mupif.DataList[mupif.String]',
        'mupif.DataList[mupif.ParticleSet]',
        'mupif.DataList[mupif.GrainState]',
        'mupif.DataList[mupif.PiecewiseLinFunction]'
    ]
    Type_ID: DataID
    Obj_ID: Optional[Union[str, List[str]]] = None
    Name: str
    ValueType: Literal['Scalar', 'Vector', 'Tensor', 'ScalarArray', 'VectorArray', 'TensorArray', ''] = ''
    Description: str = ''
    Units: str
    Required: bool = False

    @pydantic.model_validator(mode='before')
    @classmethod
    def _require_valueType_unless_property(cls, values):
        if values['Type'] != 'mupif.Property' and values['Type'] != 'mupif.TemporalProperty':
            assert 'ValueType' != ''
        return values

    @pydantic.model_validator(mode='before')
    @classmethod
    def _convert_type_id_to_value(cls, values):
        tid = values['Type_ID']
        if isinstance(tid, str):
            prefix = 'mupif.DataID.'
            if tid.startswith(prefix):
                tid = tid[len(prefix):]
            values['Type_ID'] = DataID[tid]
        return values


class InputMeta(IOMeta):
    Set_at: Literal['initialization', 'timestep']


class OutputMeta(IOMeta):
    pass



class ModelInWorkflowMeta(pydantic.BaseModel):
    'Metadata for Model as part of a workflow'
    Name: str
    Module: str = ''
    Class: str = ''
    Jobmanager: str = ''

    @pydantic.model_validator(mode='before')
    @classmethod
    def _moduleClass_or_jobmanager(cls, values):
        if values['Jobmanager'] == '':
            assert values['Module'] != '' and values['Name'] != ''
        return values


class ModelWorkflowCommonMeta(pydantic.BaseModel):
    'Metadata common for both Model and Workflow'
    Name: str
    ID: Union[str, int]
    Description: str
    Execution: ExecutionMeta
    Inputs: List[InputMeta] = []
    Outputs: List[OutputMeta] = []

class ModelMeta(ModelWorkflowCommonMeta):
    pass
    Physics: PhysicsMeta
    Solver: SolverMeta

class ModelConfiguration(pydantic.BaseModel):
     Name: str
     RequiredModelMetadata: List[str]
     OptionalModelMetadata: List[str]

# TODO: should be *Meta
class ModelConfiguration(pydantic.BaseModel):
     Name: str
     RequiredModelMetadata: List[str]
     OptionalModelMetadata: List[str]

# TODO: should be *Meta
class WorkflowConfiguration(pydantic.BaseModel):
     Name: str
     Cost: str # $, $$, or $$$
     Description: str
     Models: List[ModelConfiguration]


class WorkflowMeta(ModelWorkflowCommonMeta):
    Models: List[ModelInWorkflowMeta] = []
    ExecutionProfiles: Optional[List[WorkflowConfiguration]] = None


#ModelMeta_JSONSchema=ModelMeta.schema_json()
#WorkflowMeta_JSONSchema=WorkflowMeta.schema_json()


##
## OLD, transfer comments and delete
##


if 0:
    import copy
    # Schema for metadata for Model and further passed to Workflow
    ModelSchema = {
        "type": "object",  # Object supplies a dictionary
        "properties": {
            # Name: e.g. Non-stationary thermal problem, obtained automatically from getApplicationSignature()
            # Name of the model (or workflow), e.g. "stationary thermal model", "steel buckling workflow"
            "Name": {"type": "string"},
            # ID: Unique ID of model (workflow), e.g. "Lammps", "CalculiX", "MFEM", "Buckling workflow 1"
            "ID": {"type": ["string", "integer"]},
            "Description": {"type": "string"},
            "Version_date": {"type": "string"},
            "Material": {"type": "string"},  # What material is simulated
            "Manuf_process": {"type": "string"},  # Manufacturing process or in-service conditions
            "Geometry": {"type": "string"},  # e.g. nanometers, 3D periodic box
            "Physics": {  # Corresponds to MODA Generic Physics
                "type": "object",
                "properties": {
                    # Type: MODA model type
                    "Type": {"type": "string", "enum": ["Electronic", "Atomistic", "Molecular", "Mesoscopic", "Continuum", "Other"]},
                    "Entity": {"type": "string", "enum": ["Atom", "Electron", "Grains", "Finite volume", "Other"]},
                    # Entity_description: E.g. Atoms are treated as spherical entities in space with the radius and mass
                    # determined by the element type
                    "Entity_description": {"type": "string"},
                    # Equation: List of equations' description such as Equation of motion, heat balance, mass conservation.
                    # MODA PHYSICS EQUATIONS
                    "Equation": {"type": "array"},
                    # Equation_quantities: e.g. Force, mass, potential, energy, stress, heat, temperature.
                    "Equation_quantities": {"type": "array"},
                    # Relation_description: Describes equilibrium of forces on an infinitesimal element, etc.
                    "Relation_description": {"type": "array"},
                    # Relation_formulation: Constitutive equation (material relation), e.g. force field, stress-strain,
                    # flow-gradient. MODA MATERIAL RELATIONS
                    "Relation_formulation": {"type": "array"}
                },
                "required": ["Type", "Entity"]
            },
            "Solver": {
                "properties": {
                    # Software: Name of the software (e.g.openFOAM). Corresponds to MODA SOFTWARE TOOL
                    "Software": {"type": "string"},
                    "Language": {"type": "string"},
                    "License": {"type": "string"},
                    "Creator": {"type": "string"},
                    "Version_date": {"type": "string"},
                    # Type: Type e.g. finite difference method for Ordinary Differential Equations (ODEs)
                    # Corresponds to MODA Solver Specification NUMERICAL SOLVER attribute.
                    "Type": {"type": "string"},
                    # Solver_additional_params: Additional parameters of numerical solver, e.g. time integration scheme
                    "Solver_additional_params": {"type": "string"},
                    "Documentation": {"type": "string"},  # Where published/documented
                    "Estim_time_step_s": {"type": "number"},  # Seconds
                    "Estim_comp_time_s": {"type": "number"},  # Seconds
                    "Estim_execution_cost_EUR": {"type": "number"},  # EUR
                    "Estim_personnel_cost_EUR": {"type": "number"},  # EUR
                    "Required_expertise": {"type": "string", "enum": ["None", "User", "Expert"]},
                    "Accuracy": {"type": "string", "enum": ["Low", "Medium", "High", "Unknown"]},
                    "Sensitivity": {"type": "string", "enum": ["Low", "Medium", "High", "Unknown"]},
                    "Complexity": {"type": "string", "enum": ["Low", "Medium", "High", "Unknown"]},
                    "Robustness": {"type": "string", "enum": ["Low", "Medium", "High", "Unknown"]}
                },
                "required": [
                    "Software", "Language", "License", "Creator", "Version_date", "Type", "Documentation",
                    "Estim_time_step_s", "Estim_comp_time_s", "Estim_execution_cost_EUR", "Estim_personnel_cost_EUR",
                    "Required_expertise", "Accuracy", "Sensitivity", "Complexity", "Robustness"
                ]
            },
            "Execution": {
                "properties": {
                    "ID": {"type": ["string", "integer"]},  # Optional application execution ID (typically set by workflow)
                    # Use_case_ID: user case ID (e.g. thermo-mechanical simulation coded as 1_1)
                    "Use_case_ID": {"type": ["string", "integer"]},
                    # Task_ID: user task ID (e.g. variant of user case ID such as model with higher accuracy)
                    "Task_ID": {"type": "string"},
                    "Log_URI": {"type": "string"},
                    "Status": {"type": "string", "enum": ["Instantiated", "Initialized", "Running", "Finished", "Failed"]},
                    "Progress": {"type": "number"},  # Progress in %
                    "Date_time_start": {"type": "string"},  # automatically set in Workflow
                    "Date_time_end": {"type": "string"},  # automatically set in Workflow
                    "Timeout": {"type": "integer"},  # maximum runtime in seconds
                    "Username": {"type": "string"},  # automatically set in Model and Workflow
                    "Hostname": {"type": "string"}  # automatically set in Model and Workflow
                },
                "required": ["ID"]
            },
            "Inputs": {
                "type": "array",  # List
                "items": {
                    "type": "object",  # Object supplies a dictionary
                    "properties": {
                        "Type": {"type": "string", "enum": [
                            "mupif.Property",
                            "mupif.TemporalProperty",
                            "mupif.Field",
                            "mupif.TemporalField",
                            "mupif.HeavyStruct",
                            "mupif.PyroFile",
                            "mupif.String",
                            "mupif.ParticleSet",
                            "mupif.GrainState",
                            "mupif.Function",
                            "mupif.DataList[mupif.Property]",
                            "mupif.DataList[mupif.TemporalProperty]",
                            "mupif.DataList[mupif.Field]",
                            "mupif.DataList[mupif.TemporalField]",
                            "mupif.DataList[mupif.HeavyStruct]",
                            "mupif.DataList[mupif.String]",
                            "mupif.DataList[mupif.ParticleSet]",
                            "mupif.DataList[mupif.GrainState]",
                            "mupif.DataList[mupif.PiecewiseLinFunction]"
                        ]},
                        "Type_ID": {"type": "string", "enum": type_ids},  # e.g. PID_Concentration
                        "Obj_ID": {  # optional parameter for additional info, string or list of string
                            "anyof": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
                        },
                        "Name": {"type": "string"},
                        "ValueType": {"type": "string", "enum": ["Scalar", "Vector", "Tensor", "ScalarArray", "VectorArray", "TensorArray"]},
                        "Description": {"type": "string"},
                        "Units": {"type": "string"},
                        "Required": {"type": "boolean"},
                        "Set_at": {"type": "string", "enum": ["initialization", "timestep"]},
                        "EDMPath": {"type": "string"},
                        "EDMList": {"type": "boolean"}
                    },
                    "required": ["Type", "Type_ID", "Name", "Units", "Required", "Set_at"],
                    "allOf": [
                        {
                            "anyOf": [
                                {"required": ["ValueType"]},
                                {"allOf": [
                                    {"not": {
                                        "properties": {
                                            "Type": {"const": "mupif.Property"}
                                        }
                                    }},
                                    {"not": {
                                        "properties": {
                                            "Type": {"const": "mupif.TemporalProperty"}
                                        }
                                    }}
                                ]}

                            ]
                        }
                    ]
                }
            },
            "Outputs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Type": {"type": "string", "enum": [
                            "mupif.Property",
                            "mupif.TemporalProperty",
                            "mupif.Field",
                            "mupif.TemporalField",
                            "mupif.HeavyStruct",
                            "mupif.PyroFile",
                            "mupif.String",
                            "mupif.ParticleSet",
                            "mupif.GrainState",
                            "mupif.PiecewiseLinFunction",
                            "mupif.DataList[mupif.Property]",
                            "mupif.DataList[mupif.TemporalProperty]",
                            "mupif.DataList[mupif.Field]",
                            "mupif.DataList[mupif.TemporalField]",
                            "mupif.DataList[mupif.HeavyStruct]",
                            "mupif.DataList[mupif.String]",
                            "mupif.DataList[mupif.ParticleSet]",
                            "mupif.DataList[mupif.GrainState]",
                            "mupif.DataList[mupif.PiecewiseLinFunction]"
                        ]},
                        "Type_ID": {"type": "string", "enum": type_ids},  # e.g. mupif.DataID.FID_Temperature
                        "Obj_ID": {  # optional parameter for additional info, string or list of string
                            "anyof": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
                        },
                        "Name": {"type": "string"},
                        "ValueType": {"type": "string", "enum": ["Scalar", "Vector", "Tensor", "ScalarArray", "VectorArray", "TensorArray"]},
                        "Description": {"type": "string"},
                        "Units": {"type": "string"},
                        "EDMPath": {"type": "string"},
                        "EDMList": {"type": "boolean"}
                    },
                    "required": ["Type", "Type_ID", "Name", "Units"],
                    "allOf": [
                        {
                            "anyOf": [
                                {"required": ["ValueType"]},
                                {"allOf": [
                                    {"not": {
                                        "properties": {
                                            "Type": {"const": "mupif.Property"}
                                        }
                                    }},
                                    {"not": {
                                        "properties": {
                                            "Type": {"const": "mupif.TemporalProperty"}
                                        }
                                    }}
                                ]}

                            ]
                        }
                    ]
                }
            }
        },
        "required": [
            "Name", "ID", "Description", "Physics", "Solver", "Execution", "Inputs", "Outputs"
        ]
    }


    # reduced
    WorkflowSchema = {}
    WorkflowSchema["properties"].update({
        "Dependencies": {  # This i automatically generated according to self._models List.
            "type": "array",  # List of contained models/workflows
            "items": {
                "type": "object",  # Object supplies a dictionary
                "properties": {
                    "Label": {"type": "string"},  # Explicit label, given to the model/workflow by its parent workflow.
                    "Name": {"type": "string"},  # Obtained automatically from Model metadata.
                    "ID": {"type": ["string", "integer"]},  # Obtained automatically from Model metadata.
                    "Version_date": {"type": "string"},  # Obtained automatically from Model metadata.
                    "Type": {"type": "string", "enum": ["Model", "Workflow"]},  # Filled automatically.
                    "Dependencies": {"type": "array"}  # Object supplies a dictionary
                },
                "required": ["Name", "ID", "Version_date", "Type"]
            }
        },
        "Models": {
            "type": "array",  # List of contained models/workflows definition
            "items": {
                "type": "object",  # Object supplies a dictionary
                "properties": {
                    "Name": {"type": "string"},  # specifies access to the model using self.getModel('Name')
                    "Module": {"type": "string"},
                    "Class": {"type": "string"},
                    "Jobmanager": {"type": "string"},
                    "Instantiate": {"type": "boolean"},
                },
                "required": ["Name"],
                "anyOf": [
                    {"required": ["Module", "Class"]},  # local module with the workflow class
                    {"required": ["Jobmanager"]}  # remote model
                ]
            }
        },
        "EDMMapping": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Name": {"type": "string"},
                    "EDMEntity": {"type": "string"},
                    "DBName": {"type": "string"},
                    "createFrom": {"type": "string"},
                    "createNew": {"type": "object"},
                    "EDMList": {"type": "boolean"}
                },
                "required": ["Name", "EDMEntity", "DBName"]
            }
        },
    })
    WorkflowSchema["required"] = ["Name", "ID", "Description", "Execution", "Inputs", "Outputs", "Models"]

