class Application(object):
    """
    An abstract class representing an application and its interface (API).

    The purpose of this class is to define abstract services for data exchange and steering.
    This interface has to be implemented/provided by any application.
    The data exchange is performed by the means of new data types introduced in the framework,
    namely properties and fields. 
    New abstract data types (properties, fields) allow to hide all implementation details 
    related to discretization and data storage.
    """
    def __init__ (self, file, pyroName=None,pyroDaemon=None, pyroNS=None):
        """
        Constructor. Initializes the application.

        ARGS:
            file (str): path to application initialization file.
            pyroName(str): optional unique pyro name (i.e. application name)
            pyroDaemon(Pyro4.Daemon): optional  pyro daemon
            pyroNS(Pyro4.naming.Nameserver): optional nameserver
        """
        self.pyroName = pyroName
        self.pyroDaemon = pyroDaemon
        self.pyroNS = pyroNS

    def getField(self, fieldID, time):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        ARGS:
            fieldID (FieldID):  identifier
            time (double): target time
        Returns:
            Returns requested field (Field).
        """
    def getFieldURI(self, fieldID, time):
        """
        Returns the uri of requested field at given time. Field is identified by fieldID.

        ARGS:
            fieldID (FieldID):  identifier
            time (double): target time
        Returns:
            Returns requested field uri (Pyro4.core.URI).
        """
        field = self.getField(fieldID, time)
        uri    = self.pyroDaemon.register(field, force=True)
        #self.pyroNS.register("MUPIF."+self.pyroName+"."+str(fieldID), uri)
        return uri
    
    def setField(self, field):
        """
        Registers the given (remote) field in application. 

        ARGS:
            field (Field): remote field to be registered by the application
        """
    def getProperty(self, propID, time, objectID=0):
        """
        Returns property identified by its ID evaluated at given time.

        ARGS:
            propID (PropertyID):   property ID
            time(double):   time when property to be evaluated
            objectID (int): identifies object/submesh on which property is evaluated (optional)

        RETURNS:
            Returns representation of requested property (Property). 
        """
    def setProperty(self, property, objectID=0):
        """
        Register given property in the application
        ARGS:
            property (Property): the property class
            objectID (int):identifies object/submesh on which property is evaluated (optional)
        """
    def getFunction(self, funcID, objectID=0):
        """
        Returns function identified by its ID
        ARGS:
            funcID (FunctionID):   function ID
            objectID (int): identifies optional object/submesh
        Returns:
            Returns requested function(Function)
        """
    def setFunction(self, func, objectID=0):
        """
        Register given function in the application
        ARGS:
            func(Function): function to register
            objectID (int): identifies optional object/submesh
        """
    def getMesh (self, tstep):
        """
        Returns the computational mesh for given solution step.
        ARGS:
            tstep(TimeStep): solution step
        RETURNS:
            Returns the representation of mesh (Mesh)
        """
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        """ 
        Solves the problem for given time step.

        Proceeds the solution from actual state to given time.
        The actual state should not be updated at the end, as this method could be 
        called multiple times for the same solution step until the global convergence
        is reached. When global convergence is reached, finishStep is called and then 
        the actual state has to be updated.
        Solution can be split into individual stages identified by optional stageID parameter. 
        In between the stages the additional data exchange can be performed.
        See also wait and isSolved services.

        ARGS:
            tstep(TimeStep): solution step
            stageID(int): optional argument identifying solution stage
            runInBackground(bool): if set to True, the solution will run in background 
              (in separate thread or remotely), if supported.

        """
    def wait(self):
        """
        Wait until solve is completed when executed in background.
        """
    def isSolved(self):
        """
        Returns true or false depending whether solve has completed when executed in background.
        """ 
    def finishStep(self, tstep):
        """
        Called after a global convergence within a time step is achieved.

        ARGS:
             tstep(TimeStep): solution step
       
        """
    def getCriticalTimeStep(self):
        """
        Returns the actual (related to current state) critical time step increment (double).
        """
    def getAssemblyTime(self, tstep):
        """
        Returns the assembly time related to given time step.
        The registered fields (inputs) should be evaluated in this time.

        ARGS:
             tstep(TimeStep): solution step
        """
    def storeState(self, tstep):
        """
        Store the solution state of an application.

        ARGS:
             tstep(TimeStep): solution step
        
        """
    def restoreState(self, tstep):
        """
        Restore the saved state of an application.
        
        ARGS:
             tstep(TimeStep): solution step
        """
    def getAPIVersion(self):
        """
        Returns the supported API version.
        """
    def getApplicationSignature(self):
        """
        Returns the application identification (string)
        """
    def terminate(self):
        """
        Terminates the application.
        """

