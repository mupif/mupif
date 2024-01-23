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
from builtins import object
import Pyro5.api
from . import dataid
from . import units
from . import data
from .mupifquantity import ValueType
from .property import ConstantProperty

import pydantic
from typing import Dict


class FunctionInputDefinition(pydantic.BaseModel):
    valueType: ValueType
    unit: units.Unit


@Pyro5.api.expose
class Function(data.Data):
    """
    Represents a function.

    Usage of class Function for data transfers between codes as with Field or Property is deprecated.
    It is not supposed for data transfers any more, thus becomes an auxiliary class.

    Function is an object defined by mathematical expression. Function can depend on spatial position and time.
    Derived classes should implement evaluate service by providing a corresponding expression.

    Example: f(x,t)=sin(2*3.14159265*x(1)/10.)

    .. automethod:: __init__
    """

    # return value
    dataID: dataid.DataID
    valueType: ValueType
    unit: units.Unit
    # inputs
    inputs:  dict = pydantic.Field(default_factory=dict)
    # inputs: Dict[str, FunctionInputDefinition]

    def __init__(self, *, metadata={}, **kw):
        """
        Initializes the function.

        :param DataID funcID: function ID, e.g. FuncID_ProbabilityDistribution
        :param int objectID: Optional ID of associated subdomain, default 0
        """
        super().__init__(metadata=metadata, **kw)

    def evaluate(self, p):
        """
        Evaluates the function for given parameters packed as a dictionary.

        A dictionary is container type that can store any number of Python objects,
        including other container types. Dictionaries consist of pairs (called items)
        of keys and their corresponding values.

        Example: p={'x':(1,2,3)*mupif.U.m, 't':0.005*mupif.U.s} initializes parameter dictionary contaning vector quantity under 'x' key and scalar quantity under 't' key.

        :param dictionary p: Dictionary containing function arguments (number and type depends on particular function)
        :return: Function value evaluated at given position and time
        :rtype: ConstantProperty
        """
    def getDataID(self):
        """
        Obtain function's ID.

        :return: Returns receiver's ID.
        :rtype: int
        """
