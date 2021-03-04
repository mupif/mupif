# Dictionary containing numbers
#
# These objects are meant to be used like arrays with generalized
# indices. Non-existent elements default to zero. Global operations
# are addition, subtraction, and multiplication/division by a scalar.
#
# Written by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# last revision: 2006-10-16
#

## notice added for the local copy in MuPIF
## ----------------------------------------
##
## Copyright 1997-1999 by Konrad Hinsen. All Rights Reserved.
## 
## Permission to use, copy, modify, and distribute this software and its
## documentation for any purpose and without fee is hereby granted,
## provided that the above copyright notice appear in all copies and that
## both that copyright notice and this permission notice appear in
## supporting documentation.
## 
## THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
## INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO
## EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
## CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
## USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
## OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
## PERFORMANCE OF THIS SOFTWARE.

"""
Dictionary storing numerical values
"""

from .. import dumpable
import pydantic

class NumberDict(dumpable.Dumpable):

    """
    Dictionary storing numerical values

    Constructor: NumberDict()

    An instance of this class acts like an array of number with
    generalized (non-integer) indices. A value of zero is assumed
    for undefined entries. NumberDict instances support addition,
    and subtraction with other NumberDict instances, and multiplication
    and division by scalars.
    """

    #: data storage itself
    data: dict=pydantic.Field(default_factory=dict)


    def __add__(self, other):
        sum_dict = NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys():
            sum_dict.data[key] = self.data[key]
        for key in other.data.keys():
            sum_dict.data[key] = sum_dict.data.get(key,0) + other.data[key]
        return sum_dict

    def __sub__(self, other):
        sum_dict = NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys():
            sum_dict.data[key] = self.data[key]
        for key in other.data.keys():
            sum_dict.data[key] = sum_dict.data.get(key,0) - other.data[key]
        return sum_dict

    # needed for py3k compatibility
    def __rsub__(self,other):
        ret=NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys(): ret.data[key]=-self.data[key]
        for key in other.data.keys(): ret.data[key]=other.data[key]-self.data.get(key,0)
        return ret

    def __mul__(self, other):
        new = NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys():
            new.data[key] = other*self.data[key]
        return new
    __rmul__ = __mul__

    def __floordiv__(self, other):
        new = NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys():
            new.data[key] = self.data[key]//other
        return new

    def __truediv__(self,other):
        new = NumberDict()
        if isinstance(other,dict): other=NumberDict(data=other)
        for key in self.data.keys():
            new.data[key] = self.data[key]/other
        return new
    __div__=__truediv__
