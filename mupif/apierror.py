# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

from .dumpable import Dumpable


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

