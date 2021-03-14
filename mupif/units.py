from .physics.physicalquantities import PhysicalUnit as Unit
from .physics.physicalquantities import PhysicalQuantity as Quantity
from .physics.physicalquantities import U
Q=U
from .physics.physicalquantities import findUnit, makeQuantity

if 0:
    import pydantic.fields
    import typing

    class TimeQuantity(Quantity):
        @classmethod
        def __get_validators__(cls): yield cls.validate
        @classmethod
        def validate(cls, val: 'Quantity') -> 'Quantity':
            if not isinstance(val,Quantity): raise ValueError(f"Time be a Quantity object (not a {val.__class__.__name__}).")
            if not val.isCompatible(U.s): raise ValueError(f"Quantity must have time dimension.")
            return val
        #@classmethod
        #def __modify_schema__(cls, field_schema: typing.Dict[str, typing.Any]) -> None:
        #    update_not_none(field_schema)


