import Pyro5
from pydantic.dataclasses import dataclass
from . import dumpable
from . import units
import typing
import pydantic

# @dataclass(frozen=True)
@Pyro5.api.expose
class TimeStep(dumpable.Dumpable):
    """
    Class representing a time step.
    The folowing attributes are used to characterize a time step:
    
    ||- - -||(time-dt)- - - i-th time step(dt) - - -||(time)- - - -||- - - -||(targetTime)

    Note: Individual models (applications) assemble theit governing 
    equations at specific time, called asssemblyTime, this time
    is reported by individual models. For explicit model, asssembly time
    is equal to timeStep.time-timestep.dt, for fully implicit model, 
    assembly time is equal to timeStep.time

    .. automethod:: __init__
    """

    class Config:
        frozen=True

    number: int=1
    unit: typing.Optional[units.Unit]=None
    time: units.Quantity #: Time(time at the end of time step)
    dt: units.Quantity   #: Step length (time increment)
    targetTime: units.Quantity #: target simulation time (time at the end of simulation, not of a single TimeStep)

    @pydantic.validator('time','dt','targetTime',pre=True)
    def conv_times(cls,t,values):
        if isinstance(t,units.Quantity): return t
        if 'unit' not in values or values['unit'] is None: raise ValueError(f'When giving time as {type(t).__name__} (not a Quantity), unit must be given.')
        return units.Quantity(value=t,unit=values['unit'])

    def getTime(self):
        """
        :return: Time
        :rtype:  units.Quantity
        """
        return self.time

    def getTimeIncrement(self):
        """
        :return: Time increment
        :rtype:  units.Quantity
        """
        return self.dt

    def getTargetTime(self):
        """
        :return: Target time
        :rtype:  units.Quantity
        """
        return self.targetTime

    def getNumber(self):
        """
        :return: Receiver's solution step number
        :rtype: int
        """
        return self.number
