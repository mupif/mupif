import Pyro5
import mupif.physics.physicalquantities as PQ
from pydantic.dataclasses import dataclass
from . import dumpable
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
    unit: typing.Optional[PQ.PhysicalUnit]=None
    time: PQ.PhysicalQuantity #: Time(time at the end of time step)
    dt: PQ.PhysicalQuantity   #: Step length (time increment)
    targetTime: PQ.PhysicalQuantity #: target simulation time (time at the end of simulation, not of a single TimeStep)

    @pydantic.validator('time','dt','targetTime',pre=True)
    def conv_times(cls,t,values):
        if isinstance(t,PQ.PhysicalQuantity): return t
        if 'unit' not in values: raise ValueError(f'When giving time as {type(t).__name__} (not a PhysicalQuantity), unit must be given.')
        return PQ.PhysicalQuantity(value=t,unit=values['unit'])

    def getTime(self):
        """
        :return: Time
        :rtype:  PQ.PhysicalQuantity
        """
        return self.time

    def getTimeIncrement(self):
        """
        :return: Time increment
        :rtype:  PQ.PhysicalQuantity
        """
        return self.dt

    def getTargetTime(self):
        """
        :return: Target time
        :rtype:  PQ.PhysicalQuantity
        """
        return self.targetTime

    def getNumber(self):
        """
        :return: Receiver's solution step number
        :rtype: int
        """
        return self.number
