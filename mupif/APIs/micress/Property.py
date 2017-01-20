#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#
#  CIGS example: top level script 
#
#  Copyright (C) 2014-2016 
#  Ralph Altenfeld, Access, Intzestr.5, Aachen, Germany
#  
# This script code is free software; you can redistribute it and/or
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
#

import sys
sys.path.append('../../..')

from mupif import Property as mProperty
import MICPropertyID

class Property(mProperty.Property):
    """
    Extension of the Mupif's property class
    """     
    def getUnits(self):
        """
          The unit string representation is determined by the property ID.
          
          :return: unit's representation
          :rtype: string
        """
        if ( self.units == MICPropertyID.UNIT_String ):
          return ""
        elif ( self.units == MICPropertyID.UNIT_Percent ):
          return "%"        
        elif ( self.units == MICPropertyID.UNIT_WeightPercent ):  
          return "wt %"
        elif ( self.units == MICPropertyID.UNIT_Kelvin ):
          return "K"
        elif ( self.units == MICPropertyID.UNIT_Meter ):
          return "m"        
        else:
          raise APIError.APIError('Unit Error: no representive string available')
        return ""
    
    
