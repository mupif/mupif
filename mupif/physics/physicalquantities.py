# Physical quantities with units
#
# Written by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# with contributions from Greg Ward
# last revision: 2007-5-25
#

# This file come from the ScientificPython library and is written by Konrad Hinsen
# https://bitbucket.org/khinsen/scientificpython


"""
Physical quantities with units.

This module provides a data type that represents a physical
quantity together with its unit. It is possible to add and
subtract these quantities if the units are compatible, and
a quantity can be converted to another compatible unit.
Multiplication, subtraction, and raising to integer powers
is allowed without restriction, and the result will have
the correct unit. A quantity can be raised to a non-integer
power only if the result can be represented by integer powers
of the base units.

The values of physical constants are taken from the 1986
recommended values from CODATA. Other conversion factors
(e.g. for British units) come from various sources. I can't
guarantee for the correctness of all entries in the unit
table, so use this at your own risk.
"""


# XXX
from .numberdict import NumberDict
import numpy
import re, string
from functools import reduce
import Pyro5
import collections
from mupif import dumpable
import functools
import sys

from pydantic.dataclasses import dataclass
import typing
import pydantic


def cmp(a, b):
    return (a > b) - (a < b)


def makeQuantity(value,unit): return PhysicalQuantity(value=value,unit=unit)
def makeUnit(names,factor,powers,offset=0.): return PhysicalUnit(names=names,factor=factor,powers=powers,offset=offset)

# Class definitions
@Pyro5.api.expose
class PhysicalQuantity(dumpable.Dumpable):

    """
    Physical quantity with units

    PhysicalQuantity instances allow addition, subtraction,
    multiplication, and division with each other as well as
    multiplication, division, and exponentiation with numbers.
    Addition and subtraction check that the units of the two operands
    are compatible and return the result in the units of the first
    operand. A limited set of mathematical functions (from module
    Numeric) is applicable as well:

    * sqrt: equivalent to exponentiation with 0.5.

    * sin, cos, tan: applicable only to objects whose unit is
        compatible with 'rad'.

    See the documentation of the physicalquantities module for a list
    of the available units.

    Here is an example on usage:

    >>> from physicalquantities import PhysicalQuantity as p  # short hand
    >>> distance1 = p('10 m')
    >>> distance2 = p('10 km')
    >>> total = distance1 + distance2
    >>> total
    PhysicalQuantity(10010.0,'m')
    >>> total.convertToUnit('km')
    >>> total.getValue()
    10.01
    >>> total.getUnitName()
    'km'
    >>> total = total.inBaseUnits()
    >>> total
    PhysicalQuantity(10010.0,'m')
    >>> 
    >>> t = p(314159., 's')
    >>> # convert to days, hours, minutes, and second:
    >>> t2 = t.inUnitsOf('d','h','min','s')
    >>> t2_print = ' '.join([str(i) for i in t2])
    >>> t2_print
    '3.0 d 15.0 h 15.0 min 59.0 s'
    >>> 
    >>> e = p('2.7 Hartree*Nav')
    >>> e.convertToUnit('kcal/mol')
    >>> e
    PhysicalQuantity(1694.2757596034764,'kcal/mol')
    >>> e = e.inBaseUnits()
    >>> str(e)
    '7088849.77818 kg*m**2/s**2/mol'
    >>> 
    >>> freeze = p('0 degC')
    >>> freeze = freeze.inUnitsOf ('degF')
    >>> str(freeze)
    '32.0 degF'
    >>> 
    m = PQ(12,'kg')
    a = PQ('0.88 km/s**2')
    F = m*a
    print F 

    #vector valued quantities:
    a = PQ((1,2,3),'m')
    scalar = PQ(2.0, 's')
    a.convertToUnit('km')
    a.inUnitsOf('dm')
    a*3.0
    a*scalar

    #
    F = F.inBaseUnits()
    print F

    print F.isCompatible('MN')
    print F.isCompatible('m')

    F.convertToUnit('MN') # convert to Mega Newton
    print F
    F = F + PQ(0.1, 'kPa*m**2') # kilo Pascal m^2
    print F
    print str(F)

    value = float(str(F).split()[0])
    print value
    """

    value: typing.Union[float,typing.List[float]]=0
    unit: 'PhysicalUnit'

    @pydantic.validator('unit',pre=True,always=True)
    def convert_unit(cls,u):
        #sys.stderr.write(f'Validating unit {u}\n')
        if isinstance(u,PhysicalUnit): return u
        #sys.stderr.write(f'findUnit(u): {findUnit(u)}\n')
        return findUnit(u)
        

    #dumpAttrs=['value','unit']

    def __old_init__(self, *args):
        """
        There are two constructor calling patterns:

            1. PhysicalQuantity(value, unit), where value is any number
            and unit is either string defining the unit or PhysicalUnit instance

            2. PhysicalQuantity(value_with_unit), where value_with_unit
            is a string that contains both the value and the unit,
            i.e. '1.5 m/s'. This form is provided for more convenient
            interactive use.

        :param args: either (value, unit) or (value_with_unit,)
        :type args: (number, C{str}) or (C{str},)
        """
        if len(args) == 2:
            self.value = args[0]
            if isPhysicalUnit(args[1]):
                self.unit = args[1]
            else:
                self.unit = findUnit(args[1])
        else:
            s = args[0].strip()
            match = PhysicalQuantity._number.match(s)
            if match is None:
                raise TypeError('No number found')
            self.value = float(match.group(0))
            self.unit = findUnit(s[len(match.group(0)):])

    _number = re.compile('[+-]?[0-9]+(\\.[0-9]*)?([eE][+-]?[0-9]+)?')

    def __str__(self):
        return str(self.value) + ' ' + self.unit.name()

    def __repr__(self):
        return (self.__class__.__name__ + '(' + repr(self.value) + ',' + 
                repr(self.unit.name()) + ')')

    def _sum(self, other, sign1, sign2):
        if not isPhysicalQuantity(other):
            raise TypeError('Incompatible types')
        factor = other.unit.conversionFactorTo(self.unit)
        if isinstance(self.value, collections.Iterable):
            new_value = tuple((sign1*v1+sign2*v2*factor for v1, v2 in zip(self.value, other.value)))
        else:
            new_value = sign1*self.value + sign2*other.value*factor
        return self.__class__(value=new_value,unit=self.unit)

    def __add__(self, other):
        return self._sum(other, 1, 1)

    __radd__ = __add__

    def __sub__(self, other):
        return self._sum(other, 1, -1)

    def __rsub__(self, other):
        return self._sum(other, -1, 1)

    def __cmp__(self, other):
        diff = self._sum(other, 1, -1)
        if isinstance(diff.value, collections.Iterable):
            return all(v == 0 for v in diff.value)
        else:
            return cmp(diff.value, 0)

    def __eq__(self, other):  # python3 stuff
        diff = self._sum(other, 1, -1)
        if isinstance(diff.value, collections.Iterable):
            return all(v == 0 for v in diff.value)
        else:
            return diff.value == 0

    def __lt__(self, other):  # python3 stuff
        diff = self._sum(other, 1, -1)
        if isinstance(diff.value, collections.Iterable):
            return all(v < 0 for v in diff.value)
        else:
            return diff.value < 0
    
    def __mul__(self, other):
        if isinstance(self.value, collections.Iterable):
            # tuple valued (vector)
            if not isPhysicalQuantity(other):
                newVal = tuple((v*other for v in self.value))
                return self.__class__(value=newVal, unit=self.unit)
            else:
                # other is physical quantity with units
                if isinstance(other.value, collections.Iterable):
                    raise TypeError('Incompatible types')
                else:
                    # scalar
                    newVal = tuple((v*other.value for v in self.value))
                    unit = self.unit*other.unit
                    return self.__class__(value=newVal, unit=unit)
        else:
            if not isPhysicalQuantity(other):
                return self.__class__(value=self.value*other, unit=self.unit)
            value = self.value*other.value
            unit = self.unit*other.unit
            if unit.isDimensionless():
                return value*unit.factor
            else:
                return self.__class__(value=value, unit=unit)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(self.value, collections.Iterable):
            # tuple valued (vector)
            if not isPhysicalQuantity(other):
                newVal = tuple((v/other for v in self.value))
                return self.__class__(value=newVal, unit=self.unit)
            else:
                # other is physical quantity with units
                if isinstance(other.value, collections.Iterable):
                    raise TypeError('Incompatible types')
                else:
                    # scalar
                    newVal = tuple((v/other.value for v in self.value))
                    unit = self.unit/other.unit
                    return self.__class__(value=newVal, unit=unit)
        else:
            if not isPhysicalQuantity(other):
                return self.__class__(value=self.value/other, unit=self.unit)
            value = self.value/other.value
            unit = self.unit/other.unit
            if unit.isDimensionless():
                return value*unit.factor
            else:
                return self.__class__(value=value, unit=unit)

    def __rtruediv__(self, other):
        if not isPhysicalQuantity(other):
            return self.__class__(value=other/self.value, unit=pow(self.unit, -1))
        value = other.value/self.value
        unit = other.unit/self.unit
        if unit.isDimensionless():
            return value*unit.factor
        else:
            return self.__class__(value=value, unit=unit)

    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __pow__(self, other):
        if isPhysicalQuantity(other):
            raise TypeError('Exponents must be dimensionless')
        return self.__class__(value=pow(self.value, other), unit=pow(self.unit, other))

    def __rpow__(self, other):
        raise TypeError('Exponents must be dimensionless')

    def __abs__(self):
        return self.__class__(value=abs(self.value), unit=self.unit)

    def __pos__(self):
        return self

    def __neg__(self):
        return self.__class__(value=-self.value, unit=self.unit)

    def __bool__(self):
        return self.value != 0

    def convertToUnit(self, unit):
        """
        Change the unit and adjust the value such that
        the combination is equivalent to the original one. The new unit
        must be compatible with the previous unit of the object.

        :param C{str} unit: a unit

        :raise TypeError: if the unit string is not a know unit or a unit incompatible with the current one
        """
        unit = findUnit(unit)
        self.value = _convertValue(self.value, self.unit, unit)
        self.unit = unit

    def inUnitsOf(self, *units):
        """
        Express the quantity in different units. If one unit is
        specified, a new PhysicalQuantity object is returned that
        expresses the quantity in that unit. If several units
        are specified, the return value is a tuple of
        PhysicalObject instances with with one element per unit such
        that the sum of all quantities in the tuple equals the the
        original quantity and all the values except for the last one
        are integers. This is used to convert to irregular unit
        systems like hour/minute/second.

        :param units: one or several units
        :type units: C{str} or sequence of C{str}

        :returns: one or more physical quantities
        :rtype: L{PhysicalQuantity} or C{tuple} of L{PhysicalQuantity}
        :raises TypeError: if any of the specified units are not compatible with the original unit
        """
        units = list(map(findUnit, units))
        if len(units) == 1:
            unit = units[0]
            value = _convertValue(self.value, self.unit, unit)
            return self.__class__(value=value, unit=unit)
        else:
            units.sort()
            result = []
            value = self.value
            unit = self.unit
            for i in range(len(units)-1, -1, -1):
                value = value*unit.conversionFactorTo(units[i])
                if i == 0:
                    rounded = value
                else:
                    rounded = _round(value)
                result.append(self.__class__(value=rounded, units=units[i]))
                value = value - rounded
                unit = units[i]
            return tuple(result)

    # Contributed by Berthold Hoellmann
    def inBaseUnits(self):
        """
        :returns: the same quantity converted to base units,  i.e. SI units in most cases
        :rtype: L{PhysicalQuantity}
        """
        new_value = self.value * self.unit.factor
        num = ''
        denom = ''
        for i in range(9):
            unit = _base_names[i]
            power = self.unit.powers[i]
            if power < 0:
                denom = denom + '/' + unit
                if power < -1:
                    denom = denom + '**' + str(-power)
            elif power > 0:
                num = num + '*' + unit
                if power > 1:
                    num = num + '**' + str(power)
        if len(num) == 0:
            num = '1'
        else:
            num = num[1:]
        return self.__class__(value=new_value, unit = num + denom)

    def isCompatible(self, unit):
        """
        :param unit: a unit
        :type unit: C{str}

        :returns: C{True} if the specified unit is compatible with the one of the quantity
        :rtype: C{bool}
        """
        unit = findUnit(unit)
        return self.unit.isCompatible(unit)

    def getValue(self):
        """Return value (float) of physical quantity (no unit)."""
        if isinstance(self.value,float): return self.value
        return tuple(self.value)

    def getUnitName(self):
        """Return unit (string) of physical quantity."""
        return self.unit.name()

    def sqrt(self):
        return pow(self, 0.5)

    def sin(self):
        if self.unit.isAngle():
            return numpy.sin(self.value * self.unit.conversionFactorTo(_unit_table['rad']))
        else:
            raise TypeError('Argument of sin must be an angle')

    def cos(self):
        if self.unit.isAngle():
            return numpy.cos(self.value * self.unit.conversionFactorTo(_unit_table['rad']))
        else:
            raise TypeError('Argument of cos must be an angle')

    def tan(self):
        if self.unit.isAngle():
            return numpy.tan(self.value * self.unit.conversionFactorTo(_unit_table['rad']))
        else:
            raise TypeError('Argument of tan must be an angle')




@Pyro5.api.expose
@functools.total_ordering
class PhysicalUnit(dumpable.Dumpable):

    """
    Physical unit

    A physical unit is defined by a name (possibly composite), a scaling
    factor, and the exponentials of each of the SI base units that enter into
    it. Units can be multiplied, divided, and raised to integer powers.
    """

    names: NumberDict=NumberDict()
    factor: float
    powers: typing.List[int]
    offset: float = 0.

    @pydantic.validator('names',always=True,pre=True)
    def names_cook(cls,n):
        if n is None: return NumberDict()
        elif isinstance(n,str):
            ret=NumberDict()
            ret.data[n]=1
            return ret
        else: return n
    @pydantic.validator('powers',always=True,pre=True)
    def powers_cook(cls,p):
        return list(p)



    def __old_init__(self, names, factor, powers, offset=0):
        """
        :param names: a dictionary mapping each name component to its
                      associated integer power (e.g. C{{'m': 1, 's': -1}})
                      for M{m/s}). As a shorthand, a string may be passed
                      which is assigned an implicit power 1.
        :type names: C{dict} or C{str}
        :param factor: a scaling factor
        :type factor: C{float}
        :param powers: the integer powers for each of the nine base units
        :type powers: C{list} of C{int}
        :param offset: an additive offset to the base unit (used only for
                       temperatures)
        :type offset: C{float}
        """
        if type(names) == type(''):
            self.names = NumberDict()
            self.names[names] = 1
        else:
            self.names = names
        self.factor = factor
        self.offset = offset
        self.powers = list(powers)


    def __repr__(self):
        return '<PhysicalUnit ' + self.name() + '>'

    __str__ = __repr__

    #
    # no longer used in Python3
    # use functools.total_ordering decorator and __lt__ and __eq__ instead
    # https://stackoverflow.com/a/8277028/761090
    #
    def __cmp__(self, other):
        if isPhysicalUnit(other):
            if self.powers != other.powers:
                raise TypeError('Incompatible units')
            return cmp(self.factor, other.factor)
        else:
            return -1

    def __eq__(self,other):
        return self.powers==other.powers and self.factor==other.factor and self.offset==other.offset and self.names==other.names
    def __lt__(self,other):
        return self.powers<other.powers or self.factor<other.factor or self.offset<other.offset and self.names<other.names

    def __mul__(self, other):
        if self.offset != 0 or (isPhysicalUnit(other) and other.offset != 0):
            raise TypeError("cannot multiply units with non-zero offset")
        if isPhysicalUnit(other):
            return PhysicalUnit(names=self.names+other.names,
                                factor=self.factor*other.factor,
                                powers=list(map(lambda a, b: a+b,
                                    self.powers, other.powers)))
        else:
            return PhysicalUnit(names=self.names+{str(other): 1},
                                factor=self.factor*other,
                                powers=self.powers,
                                offset=self.offset * other)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if self.offset != 0 or (isPhysicalUnit(other) and other.offset != 0):
            raise TypeError("cannot divide units with non-zero offset")
        if isPhysicalUnit(other):
            return PhysicalUnit(names=self.names-other.names,
                                factor=self.factor/other.factor,
                                powers=list(map(lambda a, b: a-b,
                                    self.powers, other.powers)))
        else:
            return PhysicalUnit(names=self.names+{str(other): -1},
                                factor=self.factor/other, powers=self.powers)

    def __rtruediv__(self, other):
        if self.offset != 0 or (isPhysicalUnit(other) and other.offset != 0):
            raise TypeError("cannot divide units with non-zero offset")
        if isPhysicalUnit(other):
            return PhysicalUnit(names=other.names-self.names,
                                factor=other.factor/self.factor,
                                powers=list(map(lambda a, b: a-b,
                                    other.powers, self.powers)))
        else:
            return PhysicalUnit(names={str(other): 1}-self.names,
                                factor=other/self.factor,
                                powers=list(map(lambda x: -x, self.powers)))
    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __pow__(self, other):
        if self.offset != 0:
            raise TypeError("cannot exponentiate units with non-zero offset")
        if isinstance(other, (int, numpy.integer)):
            return PhysicalUnit(names=other*self.names, factor=pow(self.factor, other),
                                powers=list(map(lambda x, p=other: x*p, self.powers)))
        if isinstance(other, float):
            inv_exp = 1./other
            rounded = int(numpy.floor(inv_exp+0.5))
            if abs(inv_exp-rounded) < 1.e-10:
                if reduce(lambda a, b: a and b,
                          map(lambda x, e=rounded: x % e == 0, self.powers)):
                    f = pow(self.factor, other)
                    p = map(lambda x, p=rounded: x/p, self.powers)
                    if reduce(lambda a, b: a and b,
                              map(lambda x, e=rounded: x%e == 0,
                                  self.names.values())):
                        names = self.names/rounded
                    else:
                        names = NumberDict()
                        if f != 1.:
                            names[str(f)] = 1
                        for i in range(len(p)):
                            names[_base_names[i]] = p[i]
                    return PhysicalUnit(names=names, factor=f, powers=list(p))
                else:
                    raise TypeError('Illegal exponent')
        raise TypeError('Only integer and inverse integer exponents allowed')

    def conversionFactorTo(self, other):
        """
        :param other: another unit
        :type other: L{PhysicalUnit}

        :returns: the conversion factor from this unit to another unit
        :rtype: C{float}
        :raises TypeError: if the units are not compatible
        """
        if self.powers != other.powers:
            raise TypeError('Incompatible units')
        if self.offset != other.offset and self.factor != other.factor:
            raise TypeError(('Unit conversion (%s to %s) cannot be expressed ' +
                             'as a simple multiplicative factor') % \
                             (self.name(), other.name()))
        return self.factor/other.factor

    def conversionTupleTo(self, other): # added 1998/09/29 GPW
        """
        :param other: another unit
        :type other: L{PhysicalUnit}

        :returns: the conversion factor and offset from this unit to another unit
        :rtype: (C{float}, C{float})
        :raises TypeError: if the units are not compatible
        """
        if self.powers != other.powers:
            raise TypeError('Incompatible units')

        # let (s1,d1) be the conversion tuple from 'self' to base units
        #   (ie. (x+d1)*s1 converts a value x from 'self' to base units,
        #   and (x/s1)-d1 converts x from base to 'self' units)
        # and (s2,d2) be the conversion tuple from 'other' to base units
        # then we want to compute the conversion tuple (S,D) from
        #   'self' to 'other' such that (x+D)*S converts x from 'self'
        #   units to 'other' units
        # the formula to convert x from 'self' to 'other' units via the
        #   base units is (by definition of the conversion tuples):
        #     ( ((x+d1)*s1) / s2 ) - d2
        #   = ( (x+d1) * s1/s2) - d2
        #   = ( (x+d1) * s1/s2 ) - (d2*s2/s1) * s1/s2
        #   = ( (x+d1) - (d1*s2/s1) ) * s1/s2
        #   = (x + d1 - d2*s2/s1) * s1/s2
        # thus, D = d1 - d2*s2/s1 and S = s1/s2
        factor = self.factor / other.factor
        offset = self.offset - (other.offset * other.factor / self.factor)
        return factor, offset

    def isCompatible(self, other):     # added 1998/10/01 GPW
        """
        :param other: another unit
        :type other: L{PhysicalUnit}

        :returns: C{True} if the units are compatible, i.e. if the powers of the base units are the same
        :rtype: C{bool}
        """
        return self.powers == other.powers

    def isDimensionless(self):
        return not reduce(lambda a, b: a or b, self.powers)

    def isAngle(self):
        return self.powers[7] == 1 and reduce(lambda a, b: a + b, self.powers) == 1

    def setName(self, name):
        self.names = NumberDict(data=dict(name=1))

    def name(self):
        num = ''
        denom = ''
        for unit in self.names.data.keys():
            power = self.names.data[unit]
            if power < 0:
                denom = denom + '/' + unit
                if power < -1:
                    denom = denom + '**' + str(-power)
            elif power > 0:
                num = num + '*' + unit
                if power > 1:
                    num = num + '**' + str(power)
        if len(num) == 0:
            num = '1'
        else:
            num = num[1:]
        return num + denom


#
PhysicalQuantity.update_forward_refs()


# Type checks

def isPhysicalUnit(x):
    """
    :param x: an object
    :type x: any

    :returns: C{True} if x is a L{PhysicalUnit}
    :rtype: C{bool}
    """
    try:
        return hasattr(x, 'factor') and hasattr(x, 'powers')
    except AttributeError:
        return False
       

def isPhysicalQuantity(x):
    """
    :param x: an object
    :type x: any

    :returns: C{True} if x is a L{PhysicalQuantity}
    :rtype: C{bool}
    """
    try:
        return hasattr(x, 'value') and hasattr(x, 'unit')
    except AttributeError:
        return False
       

def getDimensionlessUnit():
    """
    return dimensionless unit
    """
    return PhysicalUnit('',   1.0,    [0, 0, 0, 0, 0, 0, 0, 0, 0])


# Helper functions

def findUnit(unit):
    if isinstance(unit, str):
        name = unit.strip()
        unit = eval(name, _unit_table)
        for cruft in ['__builtins__', '__args__']:
            try:
                del _unit_table[cruft]
            except:
                pass

    if not isPhysicalUnit(unit):
        raise TypeError(str(unit) + ' is not a unit')
    return unit


def _round(x):
    if numpy.greater(x, 0.):
        return numpy.floor(x)
    else:
        return numpy.ceil(x)


def _convertValue(value, src_unit, target_unit):
    (factor, offset) = src_unit.conversionTupleTo(target_unit)
    if isinstance(value, collections.Iterable):
        return tuple((v+offset)*factor for v in value)
    else:
        return (value + offset) * factor


# unit tests support
def assertPhysicalUnitEqual (first, second, msg=None):
    return first.__cmp__(second)



# SI unit definitions
_base_names = ['m', 'kg', 's', 'A', 'K', 'mol', 'cd', 'rad', 'sr']

_base_units = [('m',   makeUnit('m',   1.,    [1,0,0,0,0,0,0,0,0])),
               ('g',   makeUnit('g',   0.001, [0,1,0,0,0,0,0,0,0])),
               ('s',   makeUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])),
               ('A',   makeUnit('A',   1.,    [0,0,0,1,0,0,0,0,0])),
               ('K',   makeUnit('K',   1.,    [0,0,0,0,1,0,0,0,0])),
               ('mol', makeUnit('mol', 1.,    [0,0,0,0,0,1,0,0,0])),
               ('cd',  makeUnit('cd',  1.,    [0,0,0,0,0,0,1,0,0])),
               ('rad', makeUnit('rad', 1.,    [0,0,0,0,0,0,0,1,0])),
               ('sr',  makeUnit('sr',  1.,    [0,0,0,0,0,0,0,0,1])),
               ('none',makeUnit('',  1.,    [0,0,0,0,0,0,0,0,0])),  # No units
               ]

_prefixes = [('Y',  1.e24),
             ('Z',  1.e21),
             ('E',  1.e18),
             ('P',  1.e15),
             ('T',  1.e12),
             ('G',  1.e9),
             ('M',  1.e6),
             ('k',  1.e3),
             ('h',  1.e2),
             ('da', 1.e1),
             ('d',  1.e-1),
             ('c',  1.e-2),
             ('m',  1.e-3),
             ('mu', 1.e-6),
             ('n',  1.e-9),
             ('p',  1.e-12),
             ('f',  1.e-15),
             ('a',  1.e-18),
             ('z',  1.e-21),
             ('y',  1.e-24),
             ]

_unit_table = {}

for unit in _base_units:
    _unit_table[unit[0]] = unit[1]

_help = []


def _addUnit(name, unit, comment=''):
    if name in _unit_table:
        raise KeyError('Unit ' + name + ' already defined')
    if comment:
        _help.append((name, comment, unit))
    if isinstance(unit,str):
        # sys.stderr.write('Unit is: %s\n'%str(unit))
        unit = eval(unit, _unit_table)
        for cruft in ['__builtins__', '__args__']:
            try:
                del _unit_table[cruft]
            except:
                pass
    # assert isinstance(unit,PhysicalUnit)
    #sys.stderr.write(f'_addUnit: {name}, {unit}\n')
    unit.setName(name)
    _unit_table[name] = unit


def _addPrefixed(unit):
    _help.append('Prefixed units for %s:' % unit)
    _prefixed_names = []
    for prefix in _prefixes:
        name = prefix[0] + unit
        # sys.stderr.write(name+'\n')
        _addUnit(name, prefix[1]*_unit_table[unit])
        _prefixed_names.append(name)
    _help.append(', '.join(_prefixed_names))


# SI derived units; these automatically get prefixes
_help.append('SI derived units; these automatically get prefixes:\n' +
             ', '.join([prefix + ' (%.0E)' % value for prefix, value in _prefixes]) + '\n')

_unit_table['kg'] = makeUnit('kg',   1., [0, 1, 0, 0, 0, 0, 0, 0, 0])

_addUnit('Hz', '1/s', 'Hertz')
_addUnit('N', 'm*kg/s**2', 'Newton')
_addUnit('Pa', 'N/m**2', 'Pascal')
_addUnit('J', 'N*m', 'Joule')
_addUnit('W', 'J/s', 'Watt')
_addUnit('C', 's*A', 'Coulomb')
_addUnit('V', 'W/A', 'Volt')
_addUnit('F', 'C/V', 'Farad')
_addUnit('ohm', 'V/A', 'Ohm')
_addUnit('S', 'A/V', 'Siemens')
_addUnit('Wb', 'V*s', 'Weber')
_addUnit('T', 'Wb/m**2', 'Tesla')
_addUnit('H', 'Wb/A', 'Henry')
_addUnit('lm', 'cd*sr', 'Lumen')
_addUnit('lx', 'lm/m**2', 'Lux')
_addUnit('Bq', '1/s', 'Becquerel')
_addUnit('Gy', 'J/kg', 'Gray')
_addUnit('Sv', 'J/kg', 'Sievert')

del _unit_table['kg']

for unit in list(_unit_table.keys()):
    _addPrefixed(unit)

# Fundamental constants
_help.append('Fundamental constants:')

_unit_table['pi'] = numpy.pi
_addUnit('c', '299792458.*m/s', 'speed of light')
_addUnit('mu0', '4.e-7*pi*N/A**2', 'permeability of vacuum')
_addUnit('eps0', '1/mu0/c**2', 'permittivity of vacuum')
_addUnit('Grav', '6.67259e-11*m**3/kg/s**2', 'gravitational constant')
_addUnit('hplanck', '6.6260755e-34*J*s', 'Planck constant')
_addUnit('hbar', 'hplanck/(2*pi)', 'Planck constant / 2pi')
_addUnit('e', '1.60217733e-19*C', 'elementary charge')
_addUnit('me', '9.1093897e-31*kg', 'electron mass')
_addUnit('mp', '1.6726231e-27*kg', 'proton mass')
_addUnit('Nav', '6.0221367e23/mol', 'Avogadro number')
_addUnit('k', '1.380658e-23*J/K', 'Boltzmann constant')

# Time units
_help.append('Time units:')

_addUnit('min', '60*s', 'minute')
_addUnit('h', '60*min', 'hour')
_addUnit('d', '24*h', 'day')
_addUnit('wk', '7*d', 'week')
_addUnit('yr', '365.25*d', 'year')

# Length units
_help.append('Length units:')

_addUnit('inch', '2.54*cm', 'inch')
_addUnit('ft', '12*inch', 'foot')
_addUnit('yd', '3*ft', 'yard')
_addUnit('mi', '5280.*ft', '(British) mile')
_addUnit('nmi', '1852.*m', 'Nautical mile')
_addUnit('Ang', '1.e-10*m', 'Angstrom')
_addUnit('lyr', 'c*yr', 'light year')
_addUnit('Bohr', '4*pi*eps0*hbar**2/me/e**2', 'Bohr radius')

# Area units
_help.append('Area units:')

_addUnit('ha', '10000*m**2', 'hectare')
_addUnit('acres', 'mi**2/640', 'acre')
_addUnit('b', '1.e-28*m**2', 'barn')

# Volume units
_help.append('Volume units:')

_addUnit('l', 'dm**3', 'liter')
_addUnit('dl', '0.1*l', 'deci liter')
_addUnit('cl', '0.01*l', 'centi liter')
_addUnit('ml', '0.001*l', 'milli liter')
_addUnit('tsp', '4.92892159375*ml', 'teaspoon')
_addUnit('tbsp', '3*tsp', 'tablespoon')
_addUnit('floz', '2*tbsp', 'fluid ounce')
_addUnit('cup', '8*floz', 'cup')
_addUnit('pt', '16*floz', 'pint')
_addUnit('qt', '2*pt', 'quart')
_addUnit('galUS', '4*qt', 'US gallon')
_addUnit('galUK', '4.54609*l', 'British gallon')

# Mass units
_help.append('Mass units:')

_addUnit('amu', '1.6605402e-27*kg', 'atomic mass units')
_addUnit('oz', '28.349523125*g', 'ounce')
_addUnit('lb', '16*oz', 'pound')
_addUnit('ton', '2000*lb', 'ton')

# Force units
_help.append('Force units:')

_addUnit('dyn', '1.e-5*N', 'dyne (cgs unit)')

# Energy units
_help.append('Energy units:')

_addUnit('erg', '1.e-7*J', 'erg (cgs unit)')
_addUnit('eV', 'e*V', 'electron volt')
_addUnit('Hartree', 'me*e**4/16/pi**2/eps0**2/hbar**2', 'Wavenumbers/inverse cm')
_addUnit('Ken', 'k*K', 'Kelvin as energy unit')
_addUnit('cal', '4.184*J', 'thermochemical calorie')
_addUnit('kcal', '1000*cal', 'thermochemical kilocalorie')
_addUnit('cali', '4.1868*J', 'international calorie')
_addUnit('kcali', '1000*cali', 'international kilocalorie')
_addUnit('Btu', '1055.05585262*J', 'British thermal unit')

_addPrefixed('eV')

# Power units
_help.append('Power units:')

_addUnit('hp', '745.7*W', 'horsepower')

# Pressure units
_help.append('Pressure units:')

_addUnit('bar', '1.e5*Pa', 'bar (cgs unit)')
_addUnit('atm', '101325.*Pa', 'standard atmosphere')
_addUnit('torr', 'atm/760', 'torr = mm of mercury')
_addUnit('psi', '6894.75729317*Pa', 'pounds per square inch')

# Angle units
_help.append('Angle units:')

_addUnit('deg', 'pi*rad/180', 'degrees')

_help.append('Temperature units:')
# Temperature units -- can't use the 'eval' trick that _addUnit provides
# for degC and degF because you can't add units
kelvin = findUnit ('K')
_addUnit('degR', '(5./9.)*K', 'degrees Rankine')
_addUnit('degC', makeUnit(None, 1.0, kelvin.powers, 273.15), 'degrees Celcius')
_addUnit('degF', makeUnit(None, 5./9., kelvin.powers, 459.67), 'degree Fahrenheit')
del kelvin


def description():
    """Return a string describing all available units."""
    s = ''  # collector for description text
    for i,entry in enumerate(_help):
        if isinstance(entry, str):
            # headline for new section
            s += '\n' + entry + '\n'
        elif isinstance(entry, tuple):
            name, comment, unit = entry
            s += '%-8s  %-26s %s\n' % (name, comment, unit)
        else:
            # impossible
            raise TypeError('wrong construction of _help list at %d, type %s'%(i,type(entry)))
    return s


# add the description of the units to the module's doc string:
__doc__ += '\n' + description()

# Some demonstration code. Run with "python -i physicalquantities.py"
# to have this available.

# PhysicalQuantity(123,'s')

if __name__ == '__main__':

    l = PhysicalQuantity(10., 'm')
    big_l = PhysicalQuantity(10., 'km')
    print(big_l + l)
    t = PhysicalQuantity(314159., 's')
    print(t.inUnitsOf('d','h','min','s'))

    p = PhysicalQuantity # just a shorthand...

    e = p('2.7 Hartree*Nav')
    e.convertToUnit('kcal/mol')
    print(e)
    print(e.inBaseUnits())

    freeze = p('0 degC')
    print(freeze.inUnitsOf ('degF'))
