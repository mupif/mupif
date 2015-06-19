class Function(object):
        """
        Represents a function.

        Function is an object defined by mathematical expression. Function can depend on spatial position and time.
        Derived classes should implement evaluate service by providing a corresponding expression.
        
        Example: f(x,t)=sin(2*3.14159265*x(1)/10.)
        
        .. automethod:: __init__
        """
        def __init__(self, funcID, objectID=0):
            """
            Initializes the function.
            
            :param FunctionID funcID: function ID, e.g. FuncID_ProbabilityDistribution
            :param int objectID: Optional ID of associated subdomain, default 0
            """
        def evaluate (self, d):
            """
            Evaluates the function for given parameters packed as a dictionary.
            
            A dictionary is container type that can store any number of Python objects, 
            including other container types. Dictionaries consist of pairs (called items) 
            of keys and their corresponding values.
            
            Example: d={'x':(1,2,3), 't':0.005} initializes dictionary contaning tuple (vector) under 'x' key, double value 0.005 under 't' key. Some common keys: 'x': position vector 't': time

            :param dictionary d: Dictionaty containing function arguments (number and type depends on particular function)
            :return: Function value evaluated at given position and time
            :rtype: int, float, tuple
            """
        def getID (self):
            """
            :return: Returns reciver's ID.
            :rtype: int
            """
        def getObjectID(self):
            """
            :return: Returns receiver's object ID
            :rtype: int
            """
