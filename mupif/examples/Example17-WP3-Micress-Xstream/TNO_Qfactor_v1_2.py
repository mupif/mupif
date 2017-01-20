#
#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#  CIGS example: Quality factor calculation tool 
#
#  Copyright (C) 2014-2016
#  
#  Harmen Rooms
#  (Solliance, TNO, The Netherlands)
#
#  Ralph Altenfeld
#  (Access e.V., Germany)
# 
# This code is based on the Abstract and Poster/Presentation by Emmelkamp e.a. [1]
# [1] Introducing the Quality Factor as a Fast and Simple Link between PV Properties and the Crystal CIGS Structure, Jurjen Emmelkamp, Accepted poster presentation at EU PVSEC 2016 (32nd European Photovoltaic Solar Energy Conference and Exhibition), 20. - 24. June 2016, Munich Germany. 
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

import numpy as np
import math


class QFact:
    """
      This module calculates a quality factor according to
      
      'Introducing the Quality Factor as a Fast and Simple Link between PV Properties and the Crystal CIGS Structure',
      Jurjen Emmelkamp,
      Poster presentation at EU PVSEC 2016 (32nd European Photovoltaic Solar Energy Conference and Exhibition), 20. - 24. June 2016, Munich Germany. 
      
    """
        
    def __init__(self,File):
        """
          Setting the datatype and loading the lookup table
          
          :param string File: file name of the quality factor parameter table
        """
        self.dt=float
        ncol=(2,3,4,5,6)
        srow=1
        
        #check whether file exists and if yes, load parameters to calculate Q factor.
        try:
            self.table=np.loadtxt(File,usecols=ncol,skiprows=srow,dtype=self.dt,delimiter='\t')
        except Exception as e:
            raise e

    def getTable(self):
        """
        A table getter method for debug purposes.
        
        :return: table of quality factor parameters
        """
        return self.table

              
    def  calc(self,pvalues):
        """
          Calculate the quality factor
          
          :param tuple of scalars pvalues: a list of scalar property values; the order
                                           has to match the list in the quality factor parameter file
                                           which was read in the constructor.
          :return: quality factor
          :rtype: float
        """
        nparams=self.table.shape[0]
        arr_pvalues=np.array(pvalues)
        npvalues=arr_pvalues.shape[0]
        # Check whether the amount of given p values matches the amount of parameters in table. 
        if nparams!=npvalues:
            mess='the number of paramaters does not match input table'
            raise ValueError(mess)
            return
        else:
               
            rqf=1
            n=0
            for param in self.table:
                #calculating the individual quality factor and the product of IQF's 
                pv=pvalues[n]
                mn=param[0]
                opt=param[1]
                mx=param[2]
                sf=param[3]
                rf=param[4]
                
                try:
                    1/(float(sf))
                except ZeroDivisionError as e:
                    raise e
                else:
                    if ( (mn > pv) or ( pv > mx) ):
                        iqf=0
                        return float(0.0)
                    else:
                        if pv==opt:
                            rt=1
                        elif ((pv>opt) and (pv<=mx)):
                            rt=(mx-pv)/(mx-opt)
                        else:
                            rt=(pv-mn)/(opt-mn)
                        iqf=math.pow((math.pow(rt,1/float(sf))),rf)

                    rqf=rqf*iqf
                    n=n+1

        result=math.pow(rqf,1/float(nparams))
        result=round(result,4)
        return float(result)
