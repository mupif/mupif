# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#  Czech Technical University, Faculty of Civil Engineering,
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
from builtins import object

from . import CellGeometryType

class IntegrationRule(object):
    """ 
    Represent integration rule to be used on cells.
    
    .. automethod:: __init__
    """
    def __init__(self):
        return
    def getIntegrationPoints(self, cgt, npt):
        """
        Returns a list of integration points and corresponding weights.
        
        :param CellGeometryType cgt: Type of underlying cell geometry (e.g. linear triangle CGT_TRIANGLE_1)
        :param int npt: Number of desired integration points
        :return: A list of tuples containing natural coordinates of integration point and weights, i.e. [((c1_ksi, c1_eta), weight1), ((c2_ksi, c2_eta), weight2)]
        :rtype: a list of tuples
        """
    def getRequiredNumberOfPoints(self, cgt, order):
        """
        Returns required number of integration points to exactly integrate polynomial of order approxOrder on a given cell type.
        
        :param CellGeometryType cgt: Type of underlying cell geometry (e.g. linear triangle CGT_TRIANGLE_1)
        :param int order: Target polynomial order
        """

class GaussIntegrationRule(IntegrationRule):
    """ 
    Gauss integration rule.
    """
    def getIntegrationPoints(self, cgt, npt):
        """
        See :func:`IntegrationRule.getIntegrationPoints`.
        """
        if (cgt == CellGeometryType.CGT_TRIANGLE_1):
            if (npt == 1):
                return [((0.333333333333, 0.333333333333), 0.5)]
            elif (npt == 3):
                return [((0.166666666666667, 0.166666666666667),  0.166666666666667),
                        ((0.666666666666667, 0.166666666666667),  0.166666666666667),
                        ((0.166666666666667, 0.666666666666667),  0.166666666666667)]
            elif (npt == 4):
                return [((0.333333333333333, 0.333333333333333), -0.281250000000000),
                        ((0.200000000000000, 0.600000000000000),  0.260416666666667),
                        ((0.200000000000000, 0.200000000000000),  0.260416666666667),
                        ((0.600000000000000, 0.200000000000000),  0.260416666666667)]
            else:
                raise APIError.APIError("getIntegrationPoints (CGT_TRIANGLE, %d) not implemented"%(npt))
        elif (cgt == CellGeometryType.CGT_QUAD):
            if (npt == 1):
                return [((0.0, 0.0), 4.0)]
            elif (npt == 4):
                return [(( 0.577350269189626,  0.577350269189626), 1),
                        ((-0.577350269189626,  0.577350269189626), 1),
                        ((-0.577350269189626, -0.577350269189626), 1),
                        (( 0.577350269189626, -0.577350269189626), 1)]

            else:
                raise APIError.APIError("getIntegrationPoints (CGT_QUAD, %d) not implemented"%(npt))
        else:
            raise APIError.APIError("getIntegrationPoints: geometry not supported")

    def getRequiredNumberOfPoints(self, cgt, order):
        """
        See :func:`IntegrationRule.getRequiredNumberOfPoints`.
        """
        if (cgt == CellGeometryType.CGT_TRIANGLE_1):
            if ( order <= 1 ):
                return 1
            elif ( order <= 2 ):
                return 3
            elif ( order <= 3 ):
                return 4
            else:
                return -1
        elif (cgt == CellGeometryType.CGT_QUAD):
            requiredNIP = max( ( order + 1 ) / 2, 2 )
            if (requiredNIP > 4):
                return -1;
            else:
                return requiredNIP*2


