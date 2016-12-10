# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
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
from __future__ import division

debug = False

def quadratic_real (a, b, c): 
    """ 
    Finds real roots of quadratic equation: ax^2 + bx + c = 0. By substituting x = y-t and t = a/2, the equation reduces to y^2 + (b-t^2) = 0 which has easy solution y = +/-sqrt(t^2-b)

    :param float a: Parameter from quadratic equation
    :param float b: Parameter from quadratic equation
    :param float c: Parameter from quadratic equation
    :return: Two real roots if they exist
    :rtype: tuple
    """ 
    import math, cmath 
    if math.fabs(a) <= 1.e-10:
        if math.fabs(b) <= 1.e-10:
            return ()
        else:
            return (-c/float(b),)
    else:
        a, b = b / float(a), c / float(a) 
        t = a / 2.0 
        r = t**2 - b 
        if r >= 0: # real roots 
            y1 = math.sqrt(r) 
        else: # complex roots 
            return ()
        y2 = -y1 
        return (y1 - t, y2 - t)

    
