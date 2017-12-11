from builtins import object
import Pyro4
import mupif.Physics.PhysicalQuantities as PQ
import re

@Pyro4.expose
class TimeStep(object):
    """
    Class representing a time step.

    .. automethod:: __init__
    """
    def __init__(self, t, dt, targetTime, units=None, n=1):
        """
        Initializes time step.

        :param t: Time, type depends on 'units'
        :type t: float or Physics.PhysicalQuantity
        :param dt: Step length (time increment), type depends on 'units'
        :type dt: float or Physics.PhysicalQuantity
        :param targetTime: target simulation time, type depends on 'units' 
        :type targetTime: float or Physics.PhysicalQuantity
        :param Physics.PhysicalUnit units: optional units for t,dt,tarrgetTime if given as float values 
        :param int n: Optional, solution time step number, default = 1
        """
        if (PQ.isPhysicalUnit(units)):
            self.time = PQ.PhysicalQuantity(t, units)
            self.dt   = PQ.PhysicalQuantity(dt, units)
            self.targetTime = PQ.PhysicalQuantity(targetTime, units)
        else:
            
            if not PQ.isPhysicalQuantity(t):
                raise TypeError (str(t) + ' is not physical quantity')

            if not PQ.isPhysicalQuantity(dt):
                raise TypeError (str(dt) + ' is not physical quantity')

            if not PQ.isPhysicalQuantity(targetTime):
                raise TypeError (str(targetTime) + ' is not physical quantity')

            self.time = t
            self.dt = dt
            self.targetTime = targetTime
        self.number = n #solution step number
        
    def getTime(self):
        """
        :return: Time
        :rtype:  Physics.PhysicalQuantity
        """
        return self.time
    def getTimeIncrement(self):
        """
        :return: Time increment
        :rtype:  Physics.PhysicalQuantity
        """
        return self.dt
    def getTargetTime (self):
        """
        :return: Target time
        :rtype:  Physics.PhysicalQuantity
        """
        return self.targetTime
    def getNumber(self):
        """
        :return: Receiver's solution step number
        :rtype: int
        """
        return self.number
