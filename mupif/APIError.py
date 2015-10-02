class APIError(Exception):
    """
    This class serves as a base class for exceptions thrown by the framework.
    Raising an exception is a way to signal that a routine could not execute normally - for example, 
    when an input argument is invalid (e.g. value is outside of the domain of a function) 
    or when a resource it relies on is unavailable (like a missing file, a hard disk error, or out-of-memory errors)
    
    Exceptions provide a way to react to exceptional circumstances (like runtime errors) in programs by transferring 
    control to special functions called handlers. To catch exceptions, a portion of code is placed under exception inspection. This is done by enclosing that portion of code in a try-block. When an exceptional circumstance arises within that block, an exception is thrown that transfers the control to the exception handler. If no exception is thrown, the code continues normally and all handlers are ignored.

    An exception is thrown by using the throw keyword from inside the "try" block. 
    Exception handlers are declared with the keyword "except", which must be placed immediately after the try block.

    """


