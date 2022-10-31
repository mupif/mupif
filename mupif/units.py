import Pyro5.api
import astropy.units as au
import numpy as np
from astropy.units import Unit
from astropy.units import Quantity
import astropy.constants
# monkey-patches: compatibility with mupif's physical quantities
Quantity.inUnitsOf = Quantity.to
Quantity.getValue = lambda self: self.value
Quantity.getUnitName = lambda self: self.unit.to_string()
Quantity.inBaseUnits = lambda self: Quantity.si


def isCompatible(u1, u2):
    try:
        u1.to(u2)
        return True
    except Exception:
        return False


au.UnitBase.isCompatible = isCompatible
au.UnitBase.inUnitsOf = au.UnitBase.to
Quantity.isCompatible = isCompatible
def findUnit(unit): return Unit(unit)
def makeQuantity(val, unit): return Quantity(val, unit)


# for compatibility with our physical quantities
degC = au.def_unit('degC', au.deg_C)
au.add_enabled_units([
    # elementary charge is technically a constant
    au.def_unit('e', astropy.constants.si.e),
    # this is shorter
    au.def_unit('none', au.dimensionless_unscaled)
])
# enable temperature conversions by default
au.add_enabled_equivalencies(au.equivalencies.temperature())


class UnitProxy(object):
    def __getitem__(self, n): return Unit(n)
    def __getattr__(self, n): return Unit(n)


U = Q = UnitProxy()

from .dumpable import addPydanticInstanceValidator
addPydanticInstanceValidator(Quantity)
addPydanticInstanceValidator(astropy.units.UnitBase,makeKlass=astropy.units.Unit)

from .dumpable import MupifBaseModel
class RefQuantity(MupifBaseModel):
    'Quantity with data stored somewhere else. Abstract class, to be subclassed.'
    pass

# pyro serialization (this is for single-value type only)
# embedding within a dumpable is handled in dumpable.py
Pyro5.api.register_class_to_dict(au.Unit, lambda x: {'__class__': 'astropy.units.Unit', 'unit': x.to_string()})
Pyro5.api.register_dict_to_class('astropy.units.Unit', lambda cname, x: au.Unit(x['unit']))
Pyro5.api.register_class_to_dict(au.Quantity, lambda x: {'__class__': 'astropy.units.Quantity', 'value': np.array(x.value).tolist(), 'unit': x.unit.to_string()})
Pyro5.api.register_dict_to_class('astropy.units.Quantity', lambda cname, x: au.Quantity(x['value'], au.Unit(x['unit'])))


# this is to hide the warning:
#
#   WARNING: AstropyDeprecationWarning: The truth value of a Quantity is ambiguous. In the future this will raise a ValueError. [astropy.units.quantity]
#
# which comes from smart_deepcopy in pydantic (see https://github.com/samuelcolvin/pydantic/issues/4184 where the object in question raises an exception from __bool__);
# exception would be handled fine by pydantic but the warning is obnoxious
#
import warnings
warnings.filterwarnings('ignore',module='astropy.units.quantity')
