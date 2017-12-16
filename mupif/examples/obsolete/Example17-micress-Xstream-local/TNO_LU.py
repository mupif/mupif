#
#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#  CIGS example: lookup table: concentration to emissivity 
#
#  Copyright (C) 2014-2016
#  
#  Harmen Rooms
#  (Solliance, TNO, The Netherlands)
#
#  Ralph Altenfeld
#  (Access e.V., Germany)
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

class LU(object):
  """
    This module implements a lookup mechanism for a two columns table.
    A given value, e.g. SE concentration, will be mapped by 
    its position in the values range of the first column to a value in
    the second column, e.g. emissivity. Linear interpolation is used, no extrapolation.
  """

  def __init__(self,File):
    """
      The constructor read a table given as an ASCII file.
      
      :param string File: file name an ASCII table which to read in;
                          columns have to be delimited by tabulators.
      
    """
    #setting the datatype and loading the lookup table
    self.dt=float
    table=np.loadtxt(File,dtype=self.dt,delimiter='\t')
    self.xvalues=table[:,0]
    self.yvalues=table[:,1]
    return
   
  def convert(self,inputData):
    """
    Convert the input data according to the lookup table.
    
    :param inputData:  list of values to map
    :type inputData: a list of scalar values (int, float)
    :returns:  converted data
    :rtype: list of scalars (float)
    """
    Data = np.array(inputData)
    
    #preparing the result array for the output
    asize=Data.shape[0]
    result=np.empty(asize,dtype=self.dt)

    #looping through the values in the Data array to lookup the values. writing results to result array
    d = 0
    for value in Data:
      sub=self.xvalues-value
      z=np.where(sub==0)
      dim=z[0].shape
      if dim==0:
        yvalue=self.yvalues(z)
      else:
        neg=np.where(sub<0)
        #ln=neg[0].shape[0]  # RA: ln should be an index for yvalues
        if ( neg[0].shape[0] == 0 ): # RA: no extrapolation (lower bound)
          yvalue = self.yvalues[0]
        else:
          ln = neg[0][-1]
          if ( (ln+1) >= self.yvalues.shape[0] ): # RA: no extrapolation (higher bound)
            yvalue = self.yvalues[-1]
          else:
            y0=self.yvalues[ln]
            y1=self.yvalues[ln+1]
            x0=self.xvalues[ln]
            x1=self.xvalues[ln+1]
            #yvalue = value*((y1-y0)/(x1-x0)) #This is linear interpolated. Is this OK?
            yvalue = (value-x0)*((y1-y0)/(x1-x0)) + y0 # RA: interpolate in the interval
          
      result[d]=yvalue 
      d=d+1
   
    return result.tolist()
      
