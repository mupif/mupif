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

def field2Image2D(field, plane='xy', elevation = (-1.e-6, 1.e-6), numX=10, numY=20, interp='linear', vertex=True, colorBar='horizontal', barRange=('NaN','NaN'), title='', xlabel='', ylabel='', fileName='', show=True, figsize = (8,4)):
    """ 
    Plots and/or saves xy graph using a matplotlib library. Works for structured and unstructured 2D/3D fields.
    It gives only basic viewing options, for aesthetic output use e.g. VTK field export with 
    postprocessors such as ParaView or Mayavi. Idea from https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#id1
    
    :param Field field : field of unknowns
    :param str plane: what plane to extract from field, valid values are 'xy', 'xz', 'yz' 
    :param tuple elevation: range of third coordinate. For example, in plane='xy' is grabs z coordinates in the range
    :param int numX : number of divisions on x graph axis
    :param int numY : number of divisions on y graph axis
    :param str interp : interpolation type when transferring to a grid. Valid values 'linear', 'nearest' or 'cubic'
    :param bool vertex : if vertices shoud be plot as points
    :param str colorBar : color bar details. Valid values '' for no colorbar, 'vertical' or 'horizontal'  
    :param tuple barRange: min and max bar range. If barRange=('NaN','NaN'), it is adjusted automatically
    :param str title : title
    :param str xlabel : x axis label
    :param str ylabel : y axis label
    :param str fileName : if nonempty, a filename is written to the disk, usually png, pdf, ps, eps and svg are supported
    :param bool show: if the plot should be showed
    :param tuple figsize : size of canvas in inches. Affects only showing a figure. Image to a file adjust one side automatically.
    
    :return: Two real roots if they exist
    :rtype: tuple
    """ 
    import numpy as np
    import math
    from scipy.interpolate import griddata
    from mupif import Mesh, Field, log
    from Field import FieldType
    import matplotlib.pyplot as plt
    if (field.getFieldType()!=FieldType.FT_vertexBased):
        log.error('Only FieldType.FT_vertexBased is supported')

    mesh = field.getMesh()
    numVertices = mesh.getNumberOfVertices()
    
    vertexPoints = np.zeros((numVertices,2))
    values = np.zeros((numVertices))
        
    if plane=='xy':
        indX = 0
        indY = 1
        elev = 2
    elif plane=='xz':
        indX = 0
        indY = 2
        elev = 1
    elif plane=='yz':
        indX = 1
        indY = 2
        elev = 0
    
    #find eligible vertex points and values
    vertexPoints = []
    vertexValue = []
    for i in range (0, numVertices):
        coords = mesh.getVertex(i).getCoordinates()
        if (coords[elev]>elevation[0] and coords[elev]<elevation[1]):
            vertexPoints.append((coords[indX], coords[indY]))
            vertexValue.append(field.giveValue(i)[0])
    
    vertexPointsArr = np.array(vertexPoints)
    vertexValueArr = np.array(vertexValue)
    
    xMin = vertexPointsArr[:,0].min()
    xMax = vertexPointsArr[:,0].max()
    yMin = vertexPointsArr[:,1].min()
    yMax = vertexPointsArr[:,1].max()
    
    print xMin, xMax, yMin, yMax 
    
    grid_x, grid_y = np.mgrid[xMin:xMax:complex(0,numX), yMin:yMax:complex(0,numY)]    
    grid_z1 = griddata(vertexPointsArr, vertexValueArr, (grid_x, grid_y), interp)
    
    plt.figure(figsize=figsize)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    #image.tight_layout()
    
    image = plt.imshow(grid_z1.T, extent=(xMin,xMax,yMin,yMax), aspect='equal')
    
    if colorBar:
        plt.colorbar(orientation=colorBar)
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if vertex == 1:
        plt.scatter(vertexPointsArr[:,0], vertexPointsArr[:,1], marker='o', c='b', s=5, zorder=10)

    #plt.axis('equal')
    #plt.gca().set_aspect('equal', adjustable='box-forced')
    
    if (isinstance(barRange[0], float) or isinstance(barRange[0], int)):
        image.set_clim(vmin=barRange[0], vmax=barRange[1])
    
    
    if fileName:
        plt.savefig(fileName, bbox_inches='tight')
    if show:
        plt.show()
    
    
    
