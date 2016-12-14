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
from __future__ import print_function
from builtins import range
from builtins import object
from . import Cell
from . import FieldID
from . import ValueType
from . import BBox
from . import APIError
import mupif #for logger
from numpy import array, arange, random, zeros
import numpy
import copy
try:
   import cPickle as pickle #faster serialization if available
except:
   import pickle
#import logging - never use it here, it causes cPickle.PicklingError: Can't pickle <type 'thread.lock'>: attribute lookup thread.lock failed

#debug flag
debug = 0

class FieldType(object):
    """
    Represent the supported values of FieldType, i.e. FT_vertexBased or FT_cellBased.
    """
    FT_vertexBased = 1
    FT_cellBased   = 2


class Field(object):
    """
    Representation of field. Field is a scalar, vector, or tensorial
    quantity defined on a spatial domain. The field, however is assumed
    to be fixed at certain time. The field can be evaluated in any spatial point
    belonging to underlying domain.

    Derived classes will implement fields defined on common discretizations,
    like fields defined on structured/unstructured FE meshes, FD grids, etc.

    .. automethod:: __init__
    .. automethod:: _evaluate
    """
    def __init__(self, mesh, fieldID, valueType, units, time, values=None, fieldType=FieldType.FT_vertexBased):
        """
        Initializes the field instance.

        :param Mesh mesh: Instance of a Mesh class representing the underlying discretization
        :param FieldID fieldID: Field type (displacement, strain, temperature ...)
        :param ValueType valueType: Type of field values (scalear, vector, tensor)
        :param obj units: Units of the field values
        :param float time: Time associated with field values
        :param list of tuples representing individual values: Field values (format dependent on a particular field type, however each individual value should be stored as tuple, even scalar value)
        :param FieldType fieldType: Optional, determines field type (values specified as vertex or cell values), default is FT_vertexBased
        """
        self.mesh = mesh
        self.fieldID = fieldID
        self.valueType = valueType
        self.time = time
        self.units = units
        self.uri = None   #pyro uri; used in distributed setting
        #self.logger = logging.getLogger()
        self.fieldType = fieldType
        if values == None:
            if (self.fieldType == FieldType.FT_vertexBased):
                ncomponents = mesh.getNumberOfVertices()
            else:
                ncomponents = mesh.getNumberOfCells()
            self.values=zeros((ncomponents, self.getRecordSize()))
        else:
            self.values = values

    @classmethod
    def loadFromLocalFile(cls,fileName):
        """
        Alternative constructor which loads instance directly from a Pickle module.

        :param str fileName: File name

        :return: Returns Field instance
        :rtype: Field
        """
        return pickle.load(open(fileName,'rb'))

    def getRecordSize(self):
        """
        Return the number of scalars per value, depending on :obj:`valueType` passed when constructing the instance.

        :return: number of scalars (1,3,9 respectively for scalar, vector, tensor)
        :rtype: int
        """
        if self.valueType==ValueType.Scalar: return 1
        elif self.valueType==ValueType.Vector: return 3
        elif self.valueType==ValueType.Tensor: return 9
        else: raise ValueError("Invalid value of Field.valueType (%d)."%self.valueType)

    def getMesh(self):
        """
        Obtain mesh.

        :return: Returns a mesh of underlying discretization
        :rtype: Mesh
        """
        return self.mesh

    def getValueType(self):
        """
        Returns ValueType of the field, e.g. scalar, vector, tensor.

        :return: Returns value type of the receiver
        :rtype: ValueType
        """
        return self.valueType

    def getFieldID(self):
        """
        Returns FieldID, e.g. FID_Displacement, FID_Temperature.

        :return: Returns field ID
        :rtype: FieldID
        """
        return self.fieldID

    def getFieldIDName(self):
        """
        Returns name of the field.

        :return: Returns fieldID name
        :rtype: string
        """
        return self.fieldID.name

    def getFieldType (self):
        """
        Returns receiver field type (values specified as vertex or cell values)

        :return: Returns fieldType id
        :rtype: FieldType
        """
        return self.fieldType

    def getTime(self):
        """
        Get time of the field.

        :return: Time of field data
        :rtype: float
        """
        return self.time

    def evaluate(self, positions, eps=0.0):
        """
        Evaluates the receiver at given spatial position(s).

        :param position: 1D/2D/3D position vectors
        :type position: tuple, a list of tuples
        :param float eps: Optional tolerance for probing whether the point belongs to a cell (should really not be used)
        :return: field value(s)
        :rtype: tuple or a list of tuples
        """
        # test if positions is a list of positions
        if isinstance(positions, list):
            ans=[]
            for pos in positions:
                ans.append(self._evaluate(pos, eps))
            return ans
        else:
            # single position passed
            return self._evaluate(positions, eps)

    def _evaluate(self, position, eps):
        """
        Evaluates the receiver at a single spatial position.

        :param tuple position: 1D/2D/3D position vector
        :param float eps: Optional tolerance
        :return: field value
        :rtype: tuple

        .. note:: This method has some issues related to https://sourceforge.net/p/mupif/tickets/22/ .
        """
        cells = self.mesh.giveCellLocalizer().giveItemsInBBox(BBox.BBox([ c-eps for c in position], [c+eps for c in position]))
        ## answer=None
        if len(cells):
            if (self.fieldType == FieldType.FT_vertexBased):
                for icell in cells:
                    try:
                        if icell.containsPoint(position):
                            if debug:
                                mupif.log.debug(icell.getVertices())
                            try:
                                answer = icell.interpolate(position, [self.values[i.number] for i in icell.getVertices()])
                            except IndexError:
                                mupif.log.error('Field::evaluate failed, inconsistent data at cell %d'%(icell.label))
                                raise
                            return answer

                    except ZeroDivisionError:
                        print('ZeroDivisionError?')
                        mupif.log.debug(icell.number, position)
                        cell.debug=1
                        mupif.log.debug(icell.containsPoint(position), icell.glob2loc(position))

                mupif.log.error('Field::evaluate - no source cell found for position ', position)
                for icell in cells:
                    mupif.log.debug(icell.number, icell.containsPoint(position), icell.glob2loc(position))


            else: #if (self.fieldType == FieldType.FT_vertexBased):
                #in case of cell based fields do compute average of cell values containing point
                #this typically happens when point is on the shared edge or vertex
                count=0
                for icell in cells:
                    if icell.containsPoint(position):
                        if debug:
                            mupif.log.debug(icell.getVertices())

                        try:
                            tmp = self.values[icell.number]
                            if count==0:
                                answer = list(tmp)
                            else:
                                for i in answer:
                                   answer = [x+y for x in answer for y in tmp]
                            count+=1

                        except IndexError:
                            mupif.log.error('Field::evaluate failed, inconsistent data at cell %d'%(icell.label))
                            mupif.log.error(icell.getVertices())
                            raise
                # end loop over icells
                if count == 0:
                    mupif.log.error('Field::evaluate - no source cell found for position %s', str(position))
                    #for icell in cells:
                    #    mupif.log.debug(icell.number, icell.containsPoint(position), icell.glob2loc(position))
                else:
                    answer = [x/count for x in answer]
                    return answer

        else:
            #no source cell found
            mupif.log.error('Field::evaluate - no source cell found for position ' + str(position))
            raise ValueError('Field::evaluate - no source cell found for position ' + str(position))

    def giveValue(self, componentID):
        """
        Returns the value associated with a given component (vertex or integration point on a cell).

        :param tuple componentID: A tuple identifying a component: vertex (vertexID,) or integration point (CellID, IPID)
        :return: The value
        :rtype: tuple
        """
        return self.values[componentID]

    def setValue(self, componentID, value):
        """
        Sets the value associated with a given component (vertex or integration point on a cell).

        :param tuple componentID: A tuple identifying a component: vertex (vertexID,) or integration point (CellID, IPID)
        :param tuple value: Value to be set for a given component

        .. Note:: If a mesh has mapping attached (a mesh view) then we have to remember value locally and record change. The source field values are updated after commit() method is invoked.
        """
        self.values[componentID] = value

    def commit(self):
        """
        Commits the recorded changes (via setValue method) to a primary field.
        """
    def getUnits(self):
        """
        :return: Returns units of the receiver
        :rtype: obj
        """
        return self.units

    def merge(self, field):
        """
        Merges the receiver with given field together. Both fields should be on different parts of the domain (can also overlap), but should refer to same underlying discretization, otherwise unpredictable results can occur.

        :param Field field: given field to merge with.
        """
        # first merge meshes
        mesh = copy.deepcopy(self.mesh)
        mesh.merge(field.mesh)
        mupif.log.debug(mesh)
        # merge the field values
        # some type checking first
        if (self.fieldType != field.fieldType):
            raise TypeError("Field::merge: fieldType of receiver and parameter is different")
        if (self.fieldType == FieldType.FT_vertexBased):
            values=[0]*mesh.getNumberOfVertices()
            for v in range(self.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(self.mesh.getVertex(v).label)]=self.values[v]
            for v in range(field.mesh.getNumberOfVertices()):
                values[mesh.vertexLabel2Number(field.mesh.getVertex(v).label)]=field.values[v]
        else:
            values=[0]*mesh.getNumberOfCells()
            for v in range(self.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(self.mesh.giveCell(v).label)]=self.values[v]
            for v in range(field.mesh.getNumberOfCells()):
                values[mesh.cellLabel2Number(field.mesh.giveCell(v).label)]=field.values[v]

        self.mesh=mesh
        self.values=values

    def field2VTKData (self,name=None,lookupTable=None):
        """
        Creates VTK representation of the receiver. Useful for visualization. Requires pyvtk module.

        :param str name: human-readable name of the field
        :param pyvtk.LookupTable lookupTable: color lookup table
        :return: Instance of pyvtk
        :rtype: pyvtk
        """
        import pyvtk

        if name is None:
            name=self.getFieldIDName()
        if lookupTable and not isinstance(lookupTable,pyvtk.LookupTable):
            mupif.log.info('ignoring lookupTable which is not a pyvtk.LookupTable instance.')
            lookupTable=None
        if lookupTable is None:
            lookupTable=pyvtk.LookupTable([(0,.231,.298,1.0),(.4,.865,.865,1.0),(.8,.706,.016,1.0)],name='coolwarm')
            #Scalars use different name than 'coolwarm'. Then Paraview uses its own color mapping instead of taking 'coolwarm' from *.vtk file. This prevents setting Paraview's color mapping.
            scalarsKw=dict(name=name,lookup_table='default')
        else:
            scalarsKw=dict(name=name,lookup_table=lookupTable.name)
        # see http://cens.ioc.ee/cgi-bin/cvsweb/python/pyvtk/examples/example1.py?rev=1.3 for an example
        vectorsKw=dict(name=name) # vectors don't have a lookup_table

        if (self.fieldType == FieldType.FT_vertexBased):
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Scalars([val[0] for val in self.values],**scalarsKw),lookupTable),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.PointData(pyvtk.Vectors(self.values,**vectorsKw),lookupTable),
                                     'Unstructured Grid Example')
        else:
            if (self.getValueType() == ValueType.Scalar):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Scalars([val[0] for val in self.values],**scalarsKw),lookupTable),
                                     'Unstructured Grid Example')
            elif (self.getValueType() == ValueType.Vector):
                return pyvtk.VtkData(self.mesh.getVTKRepresentation(),
                                     pyvtk.CellData(pyvtk.Vectors(self.values,**vectorsKw),lookupTable),
                                     'Unstructured Grid Example')

    def dumpToLocalFile(self, fileName, protocol=pickle.HIGHEST_PROTOCOL):
        """
        Dump Field to a file using a Pickle serialization module.

        :param str fileName: File name
        :param int protocol: Used protocol - 0=ASCII, 1=old binary, 2=new binary
        """
        pickle.dump(self, open(fileName,'wb'), protocol)

    def field2Image2D(self, plane='xy', elevation = (-1.e-6, 1.e-6), numX=10, numY=20, interp='linear', fieldComponent=0, vertex=True, colorBar='horizontal', colorBarLegend='', barRange=(None,None), barFormatNum='%.3g', title='', xlabel='', ylabel='', fileName='', show=True, figsize = (8,4), matPlotFig=None):
        """ 
        Plots and/or saves 2D image using a matplotlib library. Works for structured and unstructured 2D/3D fields. 2D/3D fields need to define plane. This method gives only basic viewing options, for aesthetic and more elaborated output use e.g. VTK field export with 
        postprocessors such as ParaView or Mayavi. Idea from https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html#id1
        
        :param Field field : field of unknowns
        :param str plane: what plane to extract from field, valid values are 'xy', 'xz', 'yz' 
        :param tuple elevation: range of third coordinate. For example, in plane='xy' is grabs z coordinates in the range
        :param int numX : number of divisions on x graph axis
        :param int numY : number of divisions on y graph axis
        :param str interp : interpolation type when transferring to a grid. Valid values 'linear', 'nearest' or 'cubic'
        :param int fieldComponent: component of the field
        :param bool vertex : if vertices shoud be plot as points
        :param str colorBar : color bar details. Valid values '' for no colorbar, 'vertical' or 'horizontal'  
        :param str colorBarLegend : Legend for color bar. If '', current field name and units are printed. None prints nothing.
        :param tuple barRange: min and max bar range. If barRange=('NaN','NaN'), it is adjusted automatically
        :param str barFormatNum : format of color bar numbers
        :param str title : title
        :param str xlabel : x axis label
        :param str ylabel : y axis label
        :param str fileName : if nonempty, a filename is written to the disk, usually png, pdf, ps, eps and svg are supported
        :param bool show : if the plot should be showed
        :param tuple figsize : size of canvas in inches. Affects only showing a figure. Image to a file adjust one side automatically.
        :param obj matPlotFig : False means plot window remains in separate thread, True waits until a plot window becomes closed
        
        :return: Two real roots if they exist
        :rtype: tuple
        """ 
        try:
            import numpy as np
            import math
            from scipy.interpolate import griddata
            import matplotlib
            matplotlib.use('TkAgg')#Qt4Agg gives an empty, black window
            import matplotlib.pyplot as plt
        except ImportError as e:
            print(e)
            raise
        
        if ( self.fieldType != FieldType.FT_vertexBased):
            raise APIError.APIError ('Only FieldType.FT_vertexBased is now supported')
        
        mesh = self.getMesh()
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
            #print(coords)
            if (coords[elev]>elevation[0] and coords[elev]<elevation[1]):
                vertexPoints.append((coords[indX], coords[indY]))
                vertexValue.append(self.giveValue(i)[fieldComponent])
        
        if(len(vertexPoints)==0):
            mupif.log.info('No valid vertex points found, putting zeros on domain 1 x 1')
            for i in range(5):
                vertexPoints.append((i%2,i/4.))
                vertexValue.append(0)

        #for i in range (0, len(vertexPoints)):
            #print (vertexPoints[i], vertexValue[i])

        vertexPointsArr = np.array(vertexPoints)
        vertexValueArr = np.array(vertexValue)
        
        xMin = vertexPointsArr[:,0].min()
        xMax = vertexPointsArr[:,0].max()
        yMin = vertexPointsArr[:,1].min()
        yMax = vertexPointsArr[:,1].max()
        
        #print(xMin, xMax, yMin, yMax)
        
        grid_x, grid_y = np.mgrid[xMin:xMax:complex(0,numX), yMin:yMax:complex(0,numY)]    
        grid_z1 = griddata(vertexPointsArr, vertexValueArr, (grid_x, grid_y), interp)
        
        #print (grid_z1.T)
        
        plt.ion()#ineractive mode
        
        if matPlotFig == None:
            matPlotFig = plt.figure(figsize=figsize)
            #plt.xlim(xMin, xMax)
            #plt.ylim(yMin, yMax)
        
        plt.clf()
        plt.axis((xMin, xMax, yMin, yMax))
        image = plt.imshow(grid_z1.T, extent=(xMin,xMax,yMin,yMax), origin='lower', aspect='equal')
        #plt.margins(tight=True)
        #plt.tight_layout()
        #plt.margins(x=-0.3, y=-0.3)
        
        
        if colorBar:
            cbar = plt.colorbar(orientation=colorBar, format=barFormatNum)
            if colorBarLegend != None:
                if colorBarLegend == '':
                    colorBarLegend = self.getFieldIDName() + '_' + str(fieldComponent)
                    if self.units != None:
                        colorBarLegend = colorBarLegend + ' (' + self.units + ')'
                cbar.set_label(colorBarLegend, rotation=0 if colorBar=='horizontal' else 90)
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
            matPlotFig.canvas.draw()
            #plt.ioff()
            #plt.show(block=True)
        return matPlotFig
  
    def field2Image2DBlock(self):
        """
        Block an open window from matPlotLib. Waits until closed.
        """
        import matplotlib.pyplot as plt
        plt.ioff()
        plt.show(block=True)

    def toHdf5(self,fileName,group='component1/part1'):
        """
        Dump field to HDF5, in a simple format suitable for interoperability (TODO: document).

        :param str fileName: HDF5 file
        :param str group: HDF5 group the data will be saved under.

        The HDF hierarchy is like this::

            group
              |
              +--- mesh_01 {hash=25aa0aa04457}
              |      +--- [vertex_coords]
              |      +--- [cell_types]
              |      \--- [cell_vertices]
              +--- mesh_02 {hash=17809e2b86ea}
              |      +--- [vertex_coords]
              |      +--- [cell_types]
              |      \--- [cell_vertices]
              +--- ...
              +--- field_01
              |      +--- -> mesh_01
              |      \--- [vertex_values]
              +--- field_02
              |      +--- -> mesh_01
              |      \--- [vertex_values]
              +--- field_03
              |      +--- -> mesh_02
              |      \--- [cell_values]
              \--- ...

        where ``plain`` names are HDF (sub)groups, ``[bracketed]`` names are datasets, ``{name=value}`` are HDF attributes, ``->`` prefix indicated HDF5 hardlink (transparent to the user); numerical suffixes (``_01``, ...) are auto-allocated. Mesh objects are hardlinked using HDF5 hardlinks if an identical mesh is already stored in the group, based on hexdigest of its full data.

        .. note:: This method has not been tested yet. The format is subject to future changes.
        """
        import h5py, hashlib
        hdf=h5py.File(fileName,'a',libver='latest')
        if group not in hdf: gg=hdf.create_group(group)
        else: gg=hdf[group]
        # raise IOError('Path "%s" is already used in "%s".'%(path,fileName))
        def lowestUnused(trsf,predicate,start=1):
            'Find the lowest unused index, where *predicate* is used to test for existence, and *trsf* transforms integer (starting at *start* and incremented until unused value is found) to whatever predicate accepts as argument. Lowest transformed value is returned.'
            import itertools,sys
            for i in itertools.count(start=start):
                t=trsf(i)
                if not predicate(t): return t
        # save mesh (not saved if there already)
        newgrp=lowestUnused(trsf=lambda i:'mesh_%02d'%i,predicate=lambda t:t in gg)
        mh5=self.getMesh().asHdf5Object(parentgroup=gg,newgroup=newgrp)

        if self.values:
            fieldGrp=hdf.create_group(lowestUnused(trsf=lambda i,group=group: group+'/field_%02d'%i,predicate=lambda t: t in hdf))
            fieldGrp['mesh']=mh5
            fieldGrp.attrs['fieldID']=self.fieldID
            fieldGrp.attrs['valueType']=self.valueType
            # string/bytes may not contain NULL when stored as string in HDF5
            # see http://docs.h5py.org/en/2.3/strings.html
            # that's why we cast to opaque type "void" and uncast using tostring before unpickling
            fieldGrp.attrs['units']=numpy.void(pickle.dumps(self.units))
            fieldGrp.attrs['time']=self.time
            if self.fieldType==FieldType.FT_vertexBased:
                val=numpy.empty(shape=(self.getMesh().getNumberOfVertices(),self.getRecordSize()),dtype=numpy.float)
                for vert in range(self.getMesh().getNumberOfVertices()): val[vert]=self.giveValue(vert)
                fieldGrp['vertex_values']=val
            elif self.fieldType==FieldType.FT_cellBased:
                # raise NotImplementedError("Saving cell-based fields to HDF5 is not yet implemented.")
                val=numpy.empty(shape=(self.getMesh().getNumberOfCells(),self.getRecordSize()),dtype=numpy.float)
                for cell in range(self.getMesh().getNumberOfCells()):
                    val[cell]=self.giveValue(cell)
                fieldGrp['cell_values']=val
            else: raise RuntimeError("Unknown fieldType %d."%(self.fieldType))

    @staticmethod
    def makeFromHdf5(fileName,group='component1/part1'):
        """
        Restore Fields from HDF5 file.

        :param str fileName: HDF5 file
        :param str group: HDF5 group the data will be read from (IOError is raised if the group does not exist).
        :return: list of new :obj:`Field` instances
        :rtype: [Field,Field,...]


        .. note:: This method has not been tested yet.
        """
        import h5py, hashlib, mupif.Mesh
        hdf=h5py.File(fileName,'r',libver='latest')
        grp=hdf[group]
        # load mesh and field data from HDF5
        meshObjs=[obj for name,obj in grp.items() if name.startswith('mesh_')]
        fieldObjs=[obj for name,obj in grp.items() if name.startswith('field_')]
        # construct all meshes as mupif objects
        meshes=[mupif.Mesh.Mesh.makeFromHdf5Object(meshObj) for meshObj in meshObjs]
        # construct all fields as mupif objects
        ret=[]
        for f in fieldObjs:
            if 'vertex_values' in f: fieldType,values=FieldType.FT_vertexBased,f['vertex_values']
            elif 'cell_values' in f: fieldType,values=FieldType.FT_cellBase,f['cell_values']
            else: ValueError("HDF5/mupif format error: unable to determine field type.")
            fieldID,valueType,units,time=FieldID(f.attrs['fieldID']),f.attrs['valueType'],f.attrs['units'].tostring(),f.attrs['time']
            if units=='': units=None # special case, handled at saving time
            else: units=pickle.loads(units)
            meshIndex=meshObjs.index(f['mesh']) # find which mesh object this field refers to
            ret.append(Field(mesh=meshes[meshIndex],fieldID=fieldID,units=units,time=time,valueType=valueType,values=values,fieldType=fieldType))
        return ret

    def toVTK2(self,fileName,format='ascii'):
        '''
        Save the instance as Unstructured Grid in VTK2 format (``.vtk``).

        :param str fileName: where to save
        :param str format: one of ``ascii`` or ``binary``
        '''
        self.field2VTKData().tofile(filename=fileName,format=format)

    @staticmethod
    def makeFromVTK2(fileName,time=0,skip=['coolwarm']):
        '''
        Return fields stored in *fileName* in the VTK2 (``.vtk``) format.

        :param str fileName: filename to load from
        :param float time: time value for created fields (time is not saved in VTK2, thus cannot be recovered)
        :param [string,] skip: file names to be skipped when reading the input file; the default value skips the default coolwarm colormap.
        '''
        import pyvtk
        from . import fieldID
        if not fileName.endswith('.vtk'): mupif.log.warn('Field.makeFromVTK2: fileName should end with .vtk, you may get in trouble (proceeding).')
        ret=[]
        try: data=pyvtk.VtkData(fileName) # this is where reading the file happens (inside pyvtk)
        except NotImplementedError:
            mupif.log.info('pyvtk fails to open (binary?) file "%s", trying through vtk.vtkGenericDataReader.'%fileName)
            return Field.makeFromVTK3(fileName,time=time,forceVersion2=True)
        ugr=data.structure
        if not isinstance(ugr,pyvtk.UnstructuredGrid): raise NotImplementedError("grid type %s is not handled by mupif (only UnstructuredGrid is)."%ugr.__class__.__name__)
        mesh=mupif.Mesh.UnstructuredMesh.makeFromPyvtkUnstructuredGrid(ugr)
        # get cell and point data
        pd,cd=data.point_data.data,data.cell_data.data
        for dd,fieldType in (pd,FieldType.FT_vertexBased),(cd,FieldType.FT_cellBased):
            for d in dd:
                # will raise KeyError if fieldID with that name is not defined
                if d.name in skip: continue
                fid=fieldID.FieldID[d.name]
                # determine the number of components using the expected number of values from the mesh
                expectedNumVal=(mesh.getNumberOfVertices() if fieldType==FieldType.FT_vertexBased else mesh.getNumberOfCells())
                nc=len(d.scalars)//expectedNumVal
                valueType=ValueType.fromNumberOfComponents(nc)
                values=[d.scalars[i*nc:i*nc+nc] for i in range(len(d.scalars))]
                ret.append(Field(
                    mesh=mesh,
                    fieldID=fid,
                    units=None, # not stored at all
                    time=time,  # not stored either, set by caller
                    valueType=valueType,
                    values=values,
                    fieldType=fieldType
                ))
        return ret


    def toVTK3(self,fileName,**kw):
        '''
        Save the instance as Unstructured Grid in VTK3 format (``.vtu``). This is a simple proxy for calling :obj:`manyToVTK3` with the instance as the only field to be saved. If multiple fields with identical mesh are to be saved in VTK3, use :obj:`manyToVTK3` directly.

        :param fileName: output file name
        :param ``**kw``: passed to :obj:`manyToVTK3`
        '''
        return self.manyToVTK3([self],fileName,**kw)

    @staticmethod
    def manyToVTK3(fields,fileName,ascii=False,compress=True):
        '''
        Save all fields passed as argument into VTK3 Unstructured Grid file (``*.vtu``).

        All *fields* must be defined on the same mesh object; exception will be raised if this is not the case.

        :param bool ascii: write numbers are ASCII in the XML-based VTU file (rather than base64-encoded binary in XML)
        :param bool compress: apply compression to the data
        '''
        import vtk
        if not fields: raise ValueError('At least one field must be passed.')
        # check if all fields are defined on the same mesh
        if len(set([f.mesh for f in fields]))!=1: raise RuntimeError('Not all fields are sharing the same Mesh object (and could not be saved to a single .vtu file')
        # convert mesh to VTK UnstructuredGrid
        mesh=fields[0].getMesh()
        vtkgrid=mesh.asVtkUnstructuredGrid()
        # add fields as arrays
        for f in fields:
            arr=vtk.vtkDoubleArray()
            arr.SetNumberOfComponents(f.getRecordSize())
            arr.SetName(f.getFieldIDName())
            assert f.getFieldType() in (FieldType.FT_vertexBased,FieldType.FT_cellBased) # other future types not handled
            if f.getFieldType()==FieldType.FT_vertexBased: nn=mesh.getNumberOfVertices()
            else: nn=mesh.getNumberOfCells()
            arr.SetNumberOfValues(nn)
            for i in range(nn): arr.SetTuple(i,f.giveValue(i))
            if f.getFieldType()==FieldType.FT_vertexBased: vtkgrid.GetPointData().AddArray(arr)
            else: vtkgrid.GetCellData().AddArray(arr)
        # write the unstructured grid to file
        writer=vtk.vtkXMLUnstructuredGridWriter()
        if compress: writer.SetCompressor(vtk.vtkZLibDataCompressor())
        if ascii: writer.SetDataModeToAscii()
        writer.SetFileName(fileName)
        # change between VTK5 and VTK6
        if vtk.vtkVersion().GetVTKMajorVersion()==6: writer.SetInputData(vtkgrid)
        else: writer.SetInput(vtkgrid)
        writer.Write()
        # finito


    @staticmethod
    def makeFromVTK3(fileName,time=0,forceVersion2=False):
        '''
        Create fields from a VTK unstructured grid file (``.vtu``, format version 3, or ``.vtp`` with *forceVersion2*); the mesh is shared between fields.

        ``vtk.vtkXMLGenericDataObjectReader`` is used to open the file (unless *forceVersion2* is set), but it is checked that contained dataset is a ``vtk.vtkUnstructuredGrid`` and an error is raised if not.

        .. note:: Units are not supported when loading from VTK, all fields will have ``None`` unit assigned.

        :param str fileName: VTK (``*.vtu``) file
        :param float time: time value for created fields (time is not saved in VTK3, thus cannot be recovered)
        :param bool forceVersion2: if ``True``, ``vtk.vtkGenericDataObjectReader`` (for VTK version 2) will be used to open the file, isntead of ``vtk.vtkXMLGenericDataObjectReader``; this also supposes *fileName* ends with ``.vtk`` (not checked, but may cause an error).
        :return: list of new :obj:`Field` instances
        :rtype: [Field,Field,...]
        '''
        import vtk
        from . import fieldID
        #rr=vtk.vtkXMLUnstructuredGridReader()
        if forceVersion2 or fileName.endswith('.vtk'): rr=vtk.vtkGenericDataObjectReader()
        else: rr=vtk.vtkXMLGenericDataObjectReader()
        rr.SetFileName(fileName)
        rr.Update()
        ugrid=rr.GetOutput()
        if not isinstance(ugrid,vtk.vtkUnstructuredGrid): raise RuntimeError("vtkDataObject read from '%s' must be a vtkUnstructuredGrid (not a %s)"%(fileName,ugrid.__class__.__name__))
        #import sys
        #sys.stderr.write(str((ugrid,ugrid.__class__,vtk.vtkUnstructuredGrid)))
        # make mesh -- implemented separately
        mesh=mupif.Mesh.UnstructuredMesh.makeFromVtkUnstructuredGrid(ugrid)
        # fields which will be returned
        ret=[]
        # get cell and point data
        cd,pd=ugrid.GetCellData(),ugrid.GetPointData()
        for data,fieldType in (pd,FieldType.FT_vertexBased),(cd,FieldType.FT_cellBased):
            for idata in range(data.GetNumberOfArrays()):
                aname,arr=pd.GetArrayName(idata),pd.GetArray(idata)
                nt=arr.GetNumberOfTuples()
                if nt==0: raise RuntimeError("Zero values in field '%s', unable to determine value type."%aname)
                t0=arr.GetTuple(0)
                valueType=ValueType.fromNumberOfComponents(len(arr.GetTuple(0)))
                # this will raise KeyError if fieldID with that name not defined
                fid=fieldID.FieldID[aname]
                # get actual values as tuples
                values=[arr.GetTuple(t) for t in range(nt)]
                ret.append(Field(
                    mesh=mesh,
                    fieldID=fid,
                    units=None, # not stored at all
                    time=time,  # not stored either, set by caller
                    valueType=valueType,
                    values=values,
                    fieldType=fieldType
                ))
        return ret


#    def __deepcopy__(self, memo):
#        """ Deepcopy operatin modified not to include attributes starting with underscore.
#            These are supposed to be the ones valid only to s specific copy of the receiver.
#            An example of these attributes are _PyroURI (injected by Application),
#            where _PyroURI contains the URI of specific object, the copy should receive
#            its own URI
#        """
#        cls = self.__class__
#        dpcpy = cls.__new__(cls)
#
#        memo[id(self)] = dpcpy
#        for attr in dir(self):
#            if not attr.startswith('_'):
#                value = getattr(self, attr)
#                setattr(dpcpy, attr, copy.deepcopy(value, memo))
#        return dpcpy
