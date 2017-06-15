#
#
#  MMP (Multiscale Modeling Platform) - EU Project
#  funded by FP7 under NMP-2013-1.4-1 call with Grant agreement no: 604279
#
#  MICRESS application interface (example version)
#  
#  Copyright (C) 2014-2016 Ralph Altenfeld
#  (Access e.V., Germany)
#  
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
sys.path.append('../../..')  # for mupif import
import os
import platform
from subprocess import *
import socket
import time as timeTime
import pyvtk

from mupif import *
import logging

import micressConfig as mConf

#Micress import
import Property
import MICPropertyID
import MICFieldID

VtkReader2.pyvtk_monkeypatch()

class micress(Application.Application):

    """
      MICRESS application interface class
      This class implements the methods of the Mupif Application class for MICRESS.
                               
    """
    
    def __init__(self, file = '', workdir = ''):
        """
          Interface contructor:
          Prepares the environment for MICRESS execution and
          initializes the interface attributes.
          
          param: string file: test case configuration file name
          param: string workdir: name of work directory
          
        """
        super(micress, self).__init__(file,workdir) # call base class
               
        # set micress execution environment:
        # only necessary when starting MICRESS directly;
        # it can be done for example in a starter script or
        # in the usual environment, too
        self.osType = platform.system()
        if ( self.osType == 'Linux' ):
          try:
            os.environ['LD_LIBRARY_PATH'] = mConf.libraryPath
          except:
            pass
        
        self.micressExec = mConf.micressExec

        try:
          os.environ['ACMICRES_LICENSE_FILE'] = mConf.micressLicense
          os.environ['LSHOST'] = mConf.thermocalcLicense
        except:
          pass

        self.locIndex = -1
        self.locationList = []
        #self.locationPath = []
        self.restart = []
        self.extension = []
        #self.machine = machine()
        self.proc = None
        self.scr = None
        self.mesh = None
        self.T0 = []
        self.T1 = []
        self.TGrad0 = []
        self.TGrad1 = []

        # results
        self.componentNames = None
        self.phaseNames = None
        self.dimensions = None
        self.t = None
        self.c = None
        self.tabF = None
        self.tabK = None
        self.logParsed = False

        self.workbench = workdir      
        self.resultFiles = None
        
        self.log = logging.getLogger()
        
        return

      
    def getApplicationSignature(self):
        """
          Get the interface and external application signature.
          
          :return: returns application signature
          :rtype: string
          
        """
        return "Micress@"+ socket.gethostbyaddr(socket.gethostname())[0]+": special project version (close to 6.252)"


    def setProperty(self, property, objectID=0):
        """
          This method stores the given property value to the interface's internal 
          data attribute.
          
          :note: All following actions, like set/get/solveStep, are relative to 
                 the property PID_RVELocation. This has to be set first to act on
                 the appropriate MICRESS simulation results.
                  
          :param Mupif.Property property: the property to set
          
        """
        if (property.getPropertyID() == MICPropertyID.PID_Temperature):
          if (self.locIndex != -1):
            self.T1[self.locIndex] = property.getValue()
          else:
            msg = 'First property to set is the RVE location!'
            log.exception(msg)
            raise APIError.APIError(msg)
        elif (property.getPropertyID() == MICPropertyID.PID_zTemperatureGradient):
          if (self.locIndex != -1):
            self.TGrad1[self.locIndex] = property.getValue()
          else:
            msg = 'First property to set is the RVE location!'
            log.exception(msg)
            raise APIError.APIError(msg)
        elif (property.getPropertyID() == MICPropertyID.PID_RVELocation):
          loc = list(property.getValue())
          found = False
          i = 0
          while ( (not found) and (i < len(self.locationList)) ):
            if ( self.locationList[i] == loc ):
              found = True
            else:
              i += 1
          self.locIndex = i
          if ( not found ):
            self.locationList.append(loc)
            self.T0.append(None)
            self.T1.append(None)
            self.TGrad0.append(None)
            self.TGrad1.append(None)
            self.restart.append(False)
            self.extension.append(0)
        else:
          msg = 'Unknown property ID'
          log.exception(msg)
          raise APIError.APIError(msg)
      
     
    def getProperty(self, propID, time, objectID=0):
        """
          This method provides the property value for the given property ID and time.
          It restores these values from interface's internal data structures.
          The parsing of the external result files is done in the private
          parse methods, e.g. __parseLogfile. This allows to grab several results
          with one file parsing step, only.
          
          :param PropertyID propID: property ID, e.g. PID_Concentration
          :param double time: simulation time
          
          :return: Property object with value set
          :rtype: Property
          
        """
        
        if ( ( propID == PropertyID.PID_Concentration ) or \
             ( propID == MICPropertyID.PID_PhaseNames ) or \
             ( propID == MICPropertyID.PID_ComponentNames ) or \
             ( propID == MICPropertyID.PID_Dimensions ) ):  
          # parse log file
          if ( self.t is None ):
            self.__parseLogfile()
          if ( len(self.t) == 0 ):
            raise APIError.APIError('No entries in log file')
            return 0
          eps = 1.0E-7
          highestTime = self.t[-1]
          if ( time-eps > highestTime ):
            self.__parseLogfile()
          if ( len(self.t) == 0 ):
            raise APIError.APIError('No entries in log file')
            return 0            

        if ( (propID == MICPropertyID.PID_PhaseFractions) or \
             (propID == MICPropertyID.PID_Temperature) ):
          # parse phase fraction result table
          if ( self.tabF is None ):
            self.__parseTabFfile()
          if ( len(self.tabF) == 0 ):
            raise APIError.APIError('No entries in result table')
            return 0
          eps = 1.0E-7
          highestTime = self.tabF[-1][0]
          if ( time-eps > highestTime ):
            self.__parseTabFfile()
          tabFEntry = None
          for entry in self.tabF:
            if ( (time-eps <= entry[0]) and (entry[0] <= time+eps) ):
              tabFEntry = entry
              break
          if ( tabFEntry is None ):
            raise APIError.APIError('No time matching entry in result table')
            return 0

        if (propID == MICPropertyID.PID_AvgGrainSizePerPhase):
          # parse grain result table (TabK)
          if ( self.tabK is None ):
            self.__parseTabKfile()
          if ( len(self.tabK) == 0 ):
            raise APIError.APIError('No entries in result table')
            return 0
          eps = 1.0E-7
          highestTime = self.tabK[-1][0]
          if ( time-eps > highestTime ):
            self.__parseTabKfile()
          tabFEntry = None
          for entry in self.tabK:
            if ( (time-eps <= entry[0]) and (entry[0] <= time+eps) ):
              tabKEntry = []
              take = False
              for val in entry[1:]:
                if ( take ):
                  tabKEntry.append(val)
                take = not take
              break
          if ( tabKEntry is None ):
            raise APIError.APIError('No time matching entry in result table')
            return 0

            
        if (propID == MICPropertyID.PID_PhaseFractions):
          return Property.Property([x*100 for x in tabFEntry[2:]], MICPropertyID.PID_PhaseFractions, ValueType.Vector, time, MICPropertyID.UNIT_Percent, 0)
        elif (propID == MICPropertyID.PID_Dimensions):
          return Property.Property(self.dimensions,MICPropertyID.PID_Dimensions, ValueType.Vector, time, MICPropertyID.UNIT_Meter, 0)
        elif (propID == MICPropertyID.PID_Temperature):
          return Property.Property(entry[1], MICPropertyID.PID_Temperature, ValueType.Scalar, time, MICPropertyID.UNIT_Kelvin, 0)
        elif (propID == MICPropertyID.PID_ComponentNames):
          return Property.Property(self.componentNames, MICPropertyID.PID_ComponentNames, ValueType.Vector, time, MICPropertyID.UNIT_String, 0)
        elif (propID == MICPropertyID.PID_PhaseNames):
          return Property.Property(self.phaseNames, MICPropertyID.PID_PhaseNames, ValueType.Vector, time, MICPropertyID.UNIT_String, 0)          
        elif (propID == MICPropertyID.PID_AvgGrainSizePerPhase):
          return Property.Property(tabKEntry, MICPropertyID.PID_AvgGrainSizePerPhase, ValueType.Vector, time, MICPropertyID.UNIT_Qubicmeter, 0)        
        elif (propID == PropertyID.PID_Concentration):
          idx = 0
          while ( idx < len(self.t) ):
            if ( (time-eps <= self.t[idx]) and (self.t[idx] <= time+eps) ):
              break
            idx += 1
          if ( idx == len(self.t) ):
            raise APIError.APIError('No time matching entry in log file')
            return 0
          return Property.Property(self.c[idx], PropertyID.PID_Concentration, ValueType.Vector, time, MICPropertyID.UNIT_WeightPercent, 0)            
        elif (propID == MICPropertyID.PID_NativeBaseFileName):
          baseFilename = self.resultFiles + "_loc_" + str(self.locIndex)
          return Property.Property(baseFilename, MICPropertyID.PID_NativeBaseFileName, ValueType.Scalar, time, MICPropertyID.UNIT_String, 0)
        elif (propID == MICPropertyID.PID_NativeFieldFileName):
          vtkFile = self.__getResultsVTKFile(time)
          return Property.Property(vtkFile, MICPropertyID.PID_NativeFieldFileName, ValueType.Scalar, time, MICPropertyID.UNIT_String, 0)
        else:
          raise APIError.APIError('Unknown property ID')


    def __getResultsVTKFile(self,time):
        """
          :private: get the MICRESS vtk file name which store the results of
                    the time step with the simulation 'time'
          
          :param double time: simulation time
          
          :return: vtk results file name
          :rtype: string
          
        """
      
        f = open(self.workbench + '/' + self.resultFiles + "_loc_" + str(self.locIndex)+ '_VTK_Time.txt','r')
        t = []
        for line in f:
            if ( line.find('#') != -1 ):
                continue
            entry = line.split()
            t.append(entry)
        f.close()

        match = ""
        for i in range(len(t)):
            entryTime = float(t[i][1])
            if ( entryTime == time ):
                match = t[i][0] # get index of vtk file
        if ( len(match) == 0 ):
            raise APIError.APIError('No property available')
            return 0
        
        vtkFile = self.resultFiles + "_loc_" + str(self.locIndex) + '_' + match + '.vtk'
        log.info('Time matching vtk file: ' + vtkFile)
        return vtkFile


    def getField(self, fieldID, time ):
        """
          This method returns a Mupif field of the MICRESS results according
          to the given 'fieldID' and 'time'.
          
          :note: This implementation of the interface supports only MICRESS
                 results written in the VTK format.
          
          :param Mupif.FieldID fieldID: ID of requested field, e.g. FID_Phase
          :param double time: simulation time
          
          :return: result field in Mupif field format 
          :rtype: Mupif.Field 
        
        """
                
        vtkFile = self.workbench + '/' + self.__getResultsVTKFile(time)
        Data = pyvtk.VtkData(vtkFile)
        log.debug(Data.header+'\n')      
        dim=[]
        dim=Data.structure.dimensions
        #Number of nodes in each direction
        nx=dim[0]
        ny=dim[1]
        nz=dim[2]
        #coordinates of the points
        coords=[]
        coords= Data.structure.get_points()
        numNodes = Data.point_data.length         
        if (self.mesh == None):
            self.mesh = VtkReader2.readMesh(numNodes,nx,ny,nz,coords)

        if ( fieldID == MICFieldID.FID_Phase ):
          field = VtkReader2.readField(self.mesh, Data, fieldID, "phas", vtkFile, 1)
        else:
          raise APIError.APIError ('Unknown field ID')
                
        return field
      
      
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        """
          This method performs a MICRESS restart which starts/continues a simulation
          until the time defined in 'tstep'. The external MICRESS application
          will always run in the background and only one instance of MICRESS will
          be running at a time. The internal 'locIndex' is an index in the list of
          different values of the RVE location property.  
          
          :note: This example will skip the steering of MICRESS itself.
                 The parameter 'stageID' and 'runInBackground' are ignored in the 
                 current implementation
        
          :param Mupif.TimeStep tstep: simulation time step including target time
          
        
        """
      
        mictime = tstep.getTime()

        if ( self.locIndex == -1 ):
          raise APIError.APIError('No RVE location specified')
               
        # check properties
        if ( self.T0[self.locIndex] == None ):
            self.T0[self.locIndex] = self.T1[self.locIndex]
            self.TGrad0[self.locIndex] = self.TGrad1[self.locIndex]

        if ( not self.resultFiles ):
          self.resultFiles = ''
          for filename in os.listdir(self.workbench):
            split = filename.split('.') 
            if ( split[1] == 'template'):
              self.resultFiles = split[0]
              break
          if ( self.resultFiles == '' ):
            raise APIError.APIError('No MICRESS driving file template found')     
       
        # generate driving file from generic
        f = open(self.workbench + '/' + self.resultFiles + '.template','r')
        temporaryDrifile = self.workbench + "/" + self.resultFiles + "_loc_" + str(self.locIndex) + "_" + str(self.extension[self.locIndex]) + '.dri'
        g = open(temporaryDrifile,"w")
        
        for line in f:
          
          # restart ?
          if ( line.find('<restart>') > -1 ):
            if ( not self.restart[self.locIndex] ):
              line = line.replace('<restart>','new')
            else:
              line = line.replace('<restart>','restart')
              
          # restart file
          if ( line.find('<restart_file>') > -1 ):
            if ( not self.restart[self.locIndex] ):
              line = line.replace('<restart_file>','')
            else:
              line = line.replace('<restart_file>',self.resultFiles + "_loc_" + str(self.locIndex))
          
          # result files
          if ( line.find('<result_files>') > -1 ):
            line = line.replace('<result_files>',self.resultFiles + "_loc_" + str(self.locIndex))

          # restart ?
          if ( line.find('<overwrite>') > -1 ):
            if ( not self.restart[self.locIndex] ):
              line = line.replace('<overwrite>','overwrite')
            else:
              line = line.replace('<overwrite>','append')
          
          # end time
          if ( line.find('<time>') > -1 ):
            line = line.replace('<time>',str(mictime))

          if ( line.find('<t0>') > -1 ):
            line = line.replace('<t0>',str(self.T0[self.locIndex]))
          if ( line.find('<t1>') > -1 ):
            line = line.replace('<t1>',str(self.T1[self.locIndex]))
          if ( line.find('<zg0>') > -1 ):
            line = line.replace('<zg0>',str(self.TGrad0[self.locIndex]))
          if ( line.find('<zg1>') > -1 ):
            line = line.replace('<zg1>',str(self.TGrad1[self.locIndex]))
                      
          g.write(line)
            
        f.close()
        g.close()
        
        # store properties
        self.T0[self.locIndex] = self.T1[self.locIndex]
        self.TGrad0[self.locIndex] = self.TGrad1[self.locIndex]
                       
        # start MICRESS
        #self.scr = open(self.workbench + "/" + self.resultFiles + "_loc_" + str(self.locIndex) + "_" + str(self.extension[self.locIndex]) +'.scr','w')
        self.log.info("solveStep with MICRESS: " + temporaryDrifile)
        #self.proc = Popen([self.micressExec,temporaryDrifile],stdout=self.scr,stderr=self.scr)
 
        self.extension[self.locIndex] += 1
        self.restart[self.locIndex] = True
        
        return
           
    def terminate(self):
        """
          This method is used to clean up an interface, e.g. terminating
          running external MICRESS instances.
          
          :note: does nothing in this example and also still experimental
          
        """
        pass
        #if not (self.proc is None):
          #process = psutil.Process(self.proc.pid)
          #for p in process.get_children(recursive=True):
            #p.kill()
          #process.kill()
        return
     
    def wait(self):
      """
        This blocking method waits for an external process of MICRESS to end.
      
        :note: not in this example; there is no external MICRESS instance to wait for.
        
      """
      #self.proc.communicate()
      #self.scr.close()
      return


    def __parseTabFfile(self):
      """
        :private: This internal method parses the MICRESS result table for phase fractions
                  and stores the data in the interface internal list 'tabF'. This list will
                  be used to in the getProperty() method.
                  
      """
      if ( self.osType == 'Linux' ):
        extension = '.TabF'
      elif ( self.osType == 'Windows' ):
        extension = '_TabF.txt'
      else:
        extension = 'unkown'                  
      f = open(self.workbench + '/' + self.resultFiles + "_loc_" + str(self.locIndex) + extension,'r')
      self.tabF = []
      for line in f:
        if ( line.find('#') != -1 ):
          continue
        columns = line.split()
        entry = []
        for strValue in columns:
          entry.append(float(strValue))
        self.tabF.append(entry)
      f.close()

    def __parseTabKfile(self):
      """
        :private: This internal method parses the MICRESS result table for grain properties
                  and stores the data in the interface internal list 'tabK'. This list will
                  be used to in the getProperty() method.
                  
      """
      if ( self.osType == 'Linux' ):
        extension = '.TabK'
      elif ( self.osType == 'Windows' ):
        extension = '_TabK.txt'
      else:
        extension = 'unkown'                  
      f = open(self.workbench + '/' + self.resultFiles + "_loc_" + str(self.locIndex) + extension,'r')
      self.tabK = []
      for line in f:
        if ( line.find('#') != -1 ):
          continue
        columns = line.split()
        entry = []
        entry.append(float(columns[0]))
        for strValue in columns[5:]:
          entry.append(float(strValue))
        self.tabK.append(entry)
      f.close()

    
    def __parseLogfile(self):
      """
        :private: This internal method parses the MICRESS log file to collect general data,
                  e.g. the dimensions of the RVE, phase and component names, etc.
                  and stores the data in the interface internal lists.
                  
      """
      if ( self.osType == 'Linux' ):
        extension = '.log'
      elif ( self.osType == 'Windows' ):
        extension = '_log.txt'
      else:
        extension = 'unkown'                  
      f = open(self.workbench + '/' + self.resultFiles + "_loc_" + str(self.locIndex) + extension,'r')

      isDimension = False
      isSpacing = False
      isComponentNames = False
      lookupComponentNames = False
      self.componentNames = []
      isPhaseNames = False
      lookupPhaseNames = False
      self.phaseNames = []
      self.t = []
      self.c = []
      lookupConcentrations = False
      self.dimensions = []
      for line in f:
        if (not isDimension):
          if ( line.find("AnzX,   AnzY,   AnzZ") != -1 ):
            isDimension = True
            dimensionLine = line.split('=')[1]
        if (not isSpacing):
          if ( line.find("deltaX, deltaY, deltaZ") != -1 ):
            isSpacing = True
            spacingLine = line.split('=')[1]
        if (not isComponentNames):
          if ( line.find("0 -> ") != -1 ):
            isComponentNames = True
            lookupComponentNames = True
        if (lookupComponentNames):
          if (line.find("->") != -1):
            self.componentNames.append(line.split('>')[1].strip())
          else:
            lookupComponentNames = False
        if ((not isPhaseNames) and (isComponentNames and not lookupComponentNames)):
          if ( line.find("0 -> ") != -1 ):
              isPhaseNames = True
              lookupPhaseNames = True
        if (lookupPhaseNames):
          if (line.find("->") != -1):
            self.phaseNames.append(line.split('>')[1].strip())
          else:
            lookupPhaseNames = False
#        if ( isPhaseNames and isComponentNames ):
        if ( line.find("Intermediate output for") != -1 ):
          lookupConcentrations = True
          ts = line.split('=')
          self.t.append(float(ts[1].split()[0]))
          cEntry = []
          cEntry.append(0.0)
          concSum = 0.0
        if ( lookupConcentrations ):
          if (line.find("Average conc.") != -1):
            cs = line.split(',')[0]
            cs = cs.split('=')[1]
            conc = float(cs.split(' ')[1])
            concSum += conc
            cEntry.append(conc)
          if (line.find("Temperature at the bottom") != -1):
            cEntry[0] = 100.0 - concSum
            self.c.append(cEntry)
            lookupConcentrations = False
      f.close()
      dims = dimensionLine.strip().split(',')
      spacings = spacingLine.strip().split(',') # in micrometer
      idx = 0
      while ( idx < len(dims) ):
        self.dimensions.append(float(dims[idx]) * float(spacings[idx]) * 1.0E-02)
        idx += 1
