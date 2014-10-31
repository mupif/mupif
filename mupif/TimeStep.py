class TimeStep(object):
    """
    Class representing time step.
    Attributes:
      time - time at the end of time step.
      delta_t - time step length
    """
    def __init__(self, t, dt, n=1):
        """
        Initializes time step.
        ARGS:
            t(double): time
            dt(double): step length (time increment)
            n(int): time step number
        """
        self.time = t
        self.dt = dt
        self.number = n #solution step number
    
    def getTime(self):
        """
        Returns time step time (double)
        """
        return self.time
    def getTimeIncrement(self):
        """
        Returns time increment (double)
        """
        return self.dt
    def getNumber(self):
        """
        Returns receiver's number (int)
        """
        return self.number
