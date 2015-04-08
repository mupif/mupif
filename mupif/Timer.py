import time

class Timer(object):
    """
    Class for measuring time.
    
    .. automethod:: __enter__
    .. automethod:: __exit__
    """
    def __enter__(self):
        """
        Remembers time at calling this function.
        """
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        """
        Remembers time at calling this function and calculates the difference to __enter__().
        """
        self.end = time.clock()
        self.interval = self.end - self.start
