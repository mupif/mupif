from __future__ import division
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

class NumberDict(dict):

    """
    Dictionary storing numerical values

    Constructor: NumberDict()

    An instance of this class acts like an array of number with
    generalized (non-integer) indices. A value of zero is assumed
    for undefined entries. NumberDict instances support addition,
    and subtraction with other NumberDict instances, and multiplication
    and division by scalars.
    """
    
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            return 0

    def __coerce__(self, other):
        if type(other) == type({}):
            other = NumberDict(other)
        return self, other

    def __add__(self, other):
        sum_dict = NumberDict()
        for key in self.keys():
            sum_dict[key] = self[key]
        for key in other.keys():
            sum_dict[key] = sum_dict[key] + other[key]
        return sum_dict

    def __sub__(self, other):
        sum_dict = NumberDict()
        for key in self.keys():
            sum_dict[key] = self[key]
        for key in other.keys():
            sum_dict[key] = sum_dict[key] - other[key]
        return sum_dict

    # needed for py3k compatibility
    def __rsub__(self,other):
       ret=NumberDict()
       for key in self.keys(): ret[key]=-self[key]
       for key in other.keys(): ret[key]=other[key]-self[key]
       return ret

    def __mul__(self, other):
        new = NumberDict()
        for key in self.keys():
            new[key] = other*self[key]
        return new
    __rmul__ = __mul__

    def __floordiv__(self, other):
        new = NumberDict()
        for key in self.keys():
            new[key] = self[key]//other
        return new

    def __truediv__(self,other):
        new = NumberDict()
        for key in self.keys():
            new[key] = self[key]/other
        return new
    __div__=__truediv__
