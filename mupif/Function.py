class Function:
        """
        Represents a function.

        Function is an object defined by mathematical expression 
        and can be a function of spatial position and time.
        Derived classes should implement evaluate service by 
        providing a corresponding expression.
        
        example:
        f(x,t)=sin(2*3.14159265*x(1)/10.)
        """
        def __init__(self, funcID, objectID=0):
            """
            Initializes the function.
            ARGS:
                funcID(FunctionID): function ID
                objectID(int): optional ID of associated subdomain.
            """
        def evaluate (self, d):
            """
            Evaluates the function for given parameters packed as dictionary.
	    A dictionary is container type that can store any number of Python objects, 
	    including other container types. Dictionaries consist of pairs (called items) 
	    of keys and their corresponding values.
	    Example: d={'x':(1,2,3), 't':0.005} initializes dictionary contaning tuple (vector) under 'x' key, 
	             double value 0.005 under 't' key.
	    Some common keys: 'x': position vector 
	                      't': time

            ARGS:
                d(dictionary): dictionaty containing function arguments (number and type depends on particular function)
            RETURNS:
                function value evaluated at given position and time.
            """
        def getID (self):
            """
            Returns reciver's ID.
	    Returns:
	       id (FunctionID)
            """
        def getObjectID(self):
            """
	    Returns:
	        returns receiver's object id (int)
            """
