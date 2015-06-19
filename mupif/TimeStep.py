class TimeStep(object):
    """
    Class representing a time step.

    .. automethod:: __init__
    """
    def __init__(self, t, dt, n=1):
        """
        Initializes time step.

        :param float t: Time
        :param float dt: Step length (time increment)
        :param int n: Optional, solution time step number, default = 1
        """
        self.time = t
        self.dt = dt
        self.number = n #solution step number
    
    def getTime(self):
        """
        :return: Time
        :rtype: float
        """
        return self.time
    def getTimeIncrement(self):
        """
        :return: Time increment
        :rtype: float
        """
        return self.dt
    def getNumber(self):
        """
        :return: Receiver's solution step number
        :rtype: int
        """
        return self.number
