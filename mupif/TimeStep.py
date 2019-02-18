from builtins import object
import Pyro4
import mupif.Physics.PhysicalQuantities as PQ
import re


@Pyro4.expose
class TimeStep(object):
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
    def __init__(self, t, dt, targetTime, units=None, n=1):
        """
        Initializes time step.

        :param t: Time(time at the end of time step)
        :type t: PQ.PhysicalQuantity
        :param dt: Step length (time increment), type depends on 'units'
        :type dt: PQ.PhysicalQuantity
        :param targetTime: target simulation time (time at the end of simulation, not of a single TimeStep)
        :type targetTime: PQ.PhysicalQuantity. targetTime is not related to particular time step rather to the material model (load duration, relaxation spectra etc.)
        :param PQ.PhysicalUnit units: optional units for t, dt, targetTime if given as float values
        :param int n: Optional, solution time step number, default = 1
        """
        self.number = n  # solution step number, dimensionless

        if units is None:
            if not PQ.isPhysicalQuantity(t):
                raise TypeError(str(t) + ' is not physical quantity')

            if not PQ.isPhysicalQuantity(dt):
                raise TypeError(str(dt) + ' is not physical quantity')

            if not PQ.isPhysicalQuantity(targetTime):
                raise TypeError(str(targetTime) + ' is not physical quantity')

            self.time = t
            self.dt = dt
            self.targetTime = targetTime    
        else:
            if PQ.isPhysicalUnit(units):
                units_temp = units
            else:
                units_temp = PQ._findUnit(units)
                
            self.time = PQ.PhysicalQuantity(t, units_temp)
            self.dt = PQ.PhysicalQuantity(dt, units_temp)
            self.targetTime = PQ.PhysicalQuantity(targetTime, units_temp)
           
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
