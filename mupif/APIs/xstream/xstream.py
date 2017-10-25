#
#
#  MMP (Multiscale Modeling Platform) - EU Project
#
#  Test case (WP3) X-stream application interface 
#  
#  Copyright (C) 2014-2016
#  
#  Luuk Thielen, Miriam del Hoyo
#  (Celsian Glass&Solar, The Netherlands)
#
#  Ralph Altenfeld
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
sys.path.append('../../..')
import os
import re
import stat
import platform
import shutil
import socket
import string
import ast
from datetime import datetime

from mupif import *

import logging

import xstreamConfig as xConf
import XStPropertyID
import XStFieldID


class xstream(Application.Application):
  
    """
    X-Stream application interface class
    This class implements the methods of the Mupif Application class for X-Stream.
    
    :note: This example API uses pre-calculated results. X-Stream itself will not be started.
    
    .. automethod:: __init__
    """

    def __init__(self, file = '', workdir = ''):
        """
          Interface contructor:
          Prepares the environment for the steering 
          the external X-Stream binary, i.e. setting of variables for 
          license server and global memory size for the MPI execution.
          A copy of the binary to the working directory is done ( might be
          unnecessary, if X-Stream would be called in another way).
          Interface attributes are initialized.
          
          :param string file: test case configuration file name
          :param string workdir: name of work directory
          
        """
        super(xstream, self).__init__(file,workdir) # call base class
        
        self.log = logging.getLogger()
        
        # prepare the environment for X-Stream execution
        # NB: not necessary for this example on pre-calculated data
        #
        self.osType = platform.system()
        #os.environ['GLM_HOST'] = xConf.xstreamLicenseServer
        #os.environ['P4_GLOBMEMSIZE'] = '20000000'
        
        storePath = os.getcwd()
        os.chdir(workdir)       
        self.executable = './gtm'
        #print self.executable
        #try:
          #shutil.copyfile(
            #xConf.xstreamPath + xConf.xstreamExec,
            #self.executable )
          #os.chmod(self.executable,stat.S_IEXEC)
        #except Exception as e:
          #self.log.exception(e)
          #raise APIError.APIError('Cannot copy GTM-X exec to working directory')
          #return
        os.chdir(storePath)
        
        self.config = None
        self.file = file
        self.workdir = workdir
        self.workdirBackup = workdir
        self.casefile = None
        self.restart = False
 
        # EnsightReader variables
        self.mesh = None
        self.numberOfTimeSteps = 0
        self.timeStep = 0
        self.parts=[1, 2]
        self.partRec=[]

        self.field = None
        self.valid = False
        return

    
    def getApplicationSignature(self):
        """
          Get the interface and external application signature.
          
          :return: returns application signature
          :rtype: string
          
        """
        return "X-Stream@"+ socket.gethostbyaddr(socket.gethostname())[0]+": "+ xConf.xstreamExec
      

    def terminate(self):
        """
          Close the interface and clean up.
        
        """
        return

      
    def getField(self, fieldID):
        """
          This method reads native application results at the current 
          simulation time (see solveStep) and converts them to a
          Mupif field which will be returned.
          
          :note: In the current implementation the ID will be ignored. The field file
                 specified in the configuration will be read, i.e. for temperature.
          
          :param FieldID fieldID: ID of the field to get (see XStFieldID.py or Mupif FieldID.py)

          :return: returns Field instance
          :rtype: Field
          
        """
     
        self.__config()
        # First read geometry file if mesh does not exist
        basePath = self.workdir+'/'+xConf.ensightPath+'/'
        if (self.mesh == None):
            Geofile=basePath + self.config['geoFile']
            self.mesh = EnsightReader2.readEnsightGeo(Geofile, self.parts, self.partRec)    
    
        fileName = basePath + self.config['fieldFile'] + '.escl'
        self.log.info('Reading file '+ fileName )       
        f = EnsightReader2.readEnsightField(fileName, self.parts, self.partRec, 1, FieldID, self.mesh)
        return f


    def fieldEvaluate(self, pos, fieldID, time):
        """
          This method evaluates the Mupif field specified by its field ID
          at a given position. It combines the method calls of getField() 
          and evaluate() to stay locally to the interface and avoids a
          data transfer of the whole field.
          
          :note: This method extends the virtual Mupif application interface.
                 It returns only the value of the first position. See also
                 fieldID specific limitation of getField().
          
          :param integer fieldID: ID of the field to get values from
          :param position: 1D/2D/3D position vectors
          :type position: tuple, a list of tuples
          :param float time: the field as it was at time will be evaluated. Ignored: see getField()

          :return: field value at first position
          :rtype: field value type
        """
        self.__config()
        if ( not self.valid ):
          self.field = self.getField(fieldID, time)
          self.valid = True
        return self.field.evaluate(pos)[0]


    def setProperty(self, property, objectID=0):
        """
          Sets the given property in the X-Stream input file for the next time step.
          According to the property ID, the specific parts of the input file
          are replaced directly (no markers).
          
          :param Mupif.Property property: the Mupif property to be set
          
        """
        self.__config()
        
        if (property.getPropertyID() == XStPropertyID.PID_Temperature):
           self.__setUniformBC(property)
        elif (property.getPropertyID() == XStPropertyID.PID_Emissivity):
           self.__setUniformBC(property)
        else:
           raise APIError.APIError ('Unknown property ID')         


    def setField(self, field, objectID=0):
        """
          Sets a given field as part of the input for the next time step of X-Stream.
          The field is written to file which is addressed in the X-Stream case file.
          This is the usual method to set 2D boundary conditions.
          
          :param Mupif.Field field: the Mupif field to be set
          
        """
        self.__config()
        
        # For a field: write the values in a text file, to be read by GTM-X

        # Set the filename
        if (field.getFieldID() == XStFieldID.FID_Temperature):
            FieldDatasetName = self.workdir + '/' + self.config['Temperature_dataset']
        elif (field.getFieldID() == XStFieldID.FID_Emissivity):            
            FieldDatasetName = self.workdir + '/' + self.config['Emissivity_dataset']         
        else:
           raise APIError.APIError ('Unknown field ID')

        f = open(FieldDatasetName,'w')           
        f.write('! field data on boundary in columns: x   y   value' + '\n')
        
        # Make a structured set of points on which to set the field value
        # xy or xz or yz
        if ( (self.config['boundary_axis1'] == 'X') and \
             (self.config['boundary_axis2'] == 'Y') ):
          mina = self.config['boundary_minx']
          maxa = self.config['boundary_maxx']
          minb = self.config['boundary_miny']
          maxb = self.config['boundary_maxy']
          fix = self.config['boundary_minz']
        elif ( (self.config['boundary_axis1'] == 'X') and \
               (self.config['boundary_axis2'] == 'Z') ):
          mina = self.config['boundary_minx']
          maxa = self.config['boundary_maxx']
          minb = self.config['boundary_minz']
          maxb = self.config['boundary_maxz']
          fix = self.config['boundary_miny']
        elif ( (self.config['boundary_axis1'] == 'Y') and \
               (self.config['boundary_axis2'] == 'Z') ):
          mina = self.config['boundary_miny']
          maxa = self.config['boundary_maxy']
          minb = self.config['boundary_minz']
          maxb = self.config['boundary_maxz']
          fix = self.config['boundary_minx']
        b = minb
        spacing = self.config['boundary_spacing']
        while (b <= maxb):
            a = mina
            while (a <= maxa):
                p = (a,b,fix)
                v = field.evaluate(p)[0]
                f.write(str(a).rjust(20) + ' ' + str(b).rjust(20) + ' ' + str(v).rjust(20) + '\n')            
                a = round(a + spacing,7)
            b = round(b + spacing, 7)
        f.close()
    
        self.__setDatasetBC(field)
    
    
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        """
          This method steers X-Stream in order to restart the current simulation
          to the simulation time given in 'tstep'.
          As an additional feature, the results can be backuped according to
          the setting in 'xstreamConfig'.
          
          :note: In the current implementation the behaviour of this method is not parameter dependent.
                 The solution will proceed a critical time step as defined in the X-Stream case file
                 (a constant step, see getCriticalTimeStep()).
                 The external X-Stream application will be run in the foreground.
          
          :note: Instead of running X-Stream in this example, the results will
                 be restored from an backup.
          
          :param Mupif.TimeStep tstep: target time; ignored
          
        """
        self.__config()
        
        self.valid = False
        self.timeStep = self.timeStep + 1
        
        storePath= os.getcwd()
        os.chdir(self.workdir)
        
        # restore from backup
        folder = './' + xConf.copyFolder + '/' + 'TimeStep_' + str(self.timeStep)
        # Copy the output files and the input files
        extensions = ['.out','.case','.escl','.cas', '.geo', '.nvect', '.evect', ]
        list_files =  [ [os.path.join(root,file),root.split(folder)[1]] for root,dirs,files in os.walk(folder) for file in files if os.path.splitext(file)[-1] in extensions ]              
        for fileve in list_files:
          folder_destination = '.'+ fileve[1]
          shutil.copy(fileve[0],folder_destination )   
      
        # Clean output file
        Outputfile=self.workdir+'/'+self.config['outputFile']        
        #if (os.path.exists(Outputfile)):
        #    os.remove(Outputfile) 
        
        # First check if all files are available   
        self.__checkInputFilesExist()
        
        ## execute X-stream
        # ATTENTION: not in this example, results will be read from a backup
        command_to_run=self.executable + ' -f ' + self.config['caseFile']
        self.log.info('solveStep with X-Stream')
        ##command_to_run=xConf.mpirun + ' -machinefile ' + \
          ##xConf.machinefile + ' -np ' + str(xConf.nbOfProcesses) + ' ' + \
          ##self.executable + ' -f ' + \
          ##self.config['caseFile']
        #print "Now running: " + command_to_run
        #print "in " + self.workdir
        #os.system(command_to_run)
        os.chdir(storePath)
        
        # Check if X-stream finished properly
        finished_OK=False   

        if (os.path.exists(Outputfile)):
           lines=open(Outputfile, 'r').readlines()           
           for line in lines: 
               if re.search( 'N o r m a l   t e r m i n a t i o n   o f   t h e   p r o g r a m', line):
                  finished_OK=True
        if (finished_OK==False ):
                raise APIError.APIError('X-stream has not finished properly. ')               
        
        self.restart = True
        self.__changeValueKeyword('READ_FROM_RESTART_FILE','True')
        
        if xConf.BackUpFiles==True:
        # copy results to a back-up folder 
            folder = self.workdir
            destination = self.workdir + '/' + xConf.copyFolder
            if not os.path.isdir(destination): #ensures the folder exists 
               os.mkdir(destination)
            
            # Copy the output files and the input files
            extensions = ['.out','.case','.escl','.cas', '.geo', '.nvect', '.evect', ]
            list_files =  [ [os.path.join(root,file),root.split(folder)[1]] for root,dirs,files in os.walk(folder) for file in files if os.path.splitext(file)[-1] in extensions ]      
            now = datetime.now().strftime('TimeStep_'+ str(self.timeStep)+'_Date'+'%Y-%m-%d-%H-%M-%S') #generate a string with data: year-month-day-Hour-Minute-Second
            folder_destination = os.path.join(destination,now)
            os.mkdir(folder_destination)

            for fileve in list_files:
              if ( not (fileve[0].find(xConf.copyFolder) > -1) ):
                folder_file = folder_destination + fileve[1]
                if not os.path.isdir(folder_file): #create the folder if it does not exist
                  os.mkdir(folder_file)
                shutil.copy(fileve[0], folder_file)   


    def getCriticalTimeStep(self):
        """
          Get the critical time step.
          This step is given in the X-Stream case file. It is the normal application
          time step.
          
          :return: float
          
        """
        self.__config()
        #gets the timestep from the .cas file
        lines = open(self.workdir + '/' + self.config['caseFile'],'r').readlines()  
        found_tstep=False        
        for line in lines: 
           if ( not line.lstrip().startswith('!') ):            
              if re.search( r"TIME_STEP ", line, re.IGNORECASE):
                 found_tstep=True 
                 value = float(line.split()[1])
                 self.log.info("The critical time step in X-stream is %f" % value)    
                 return value 

        if (found_tstep==False):
            raise APIError.APIError('The timestep (keyword TIME_STEP) can not be found')


    def __changeValueKeyword(self, word, new_value):
        """
          This method replaces the current value of the X-Stream parameter 'word'
          with the new_value in the X-Stream case file.
          
          :param string word: X-Stream keyword
          :param string new_value: new value
          
        """
        #open the file and store the lines
        filename = self.workdir + '/' + self.config['caseFile']
        f = open(filename,"r")
        #new_value=new_value.upper()
        lines = f.readlines()
        f.close()
        found_word = False               
        #empty the file and write over it
        f = open(filename,"w")
        for line in lines:  
            if ( not line.lstrip().startswith('!') ):            
               if re.search( word, line, re.IGNORECASE):
                  # found the word
                  found_word = True
                  value = line.split()[1]
                  # Change the line          
                  #line = string.replace(line, str(value), new_value , 1)#Python 2.7
                  line.replace(str(value), new_value , 1)
                  f.write(line)
               else:
                  f.write(line)
            else:
               f.write(line)
        f.close() 

        if ( not found_word ):
           raise APIError.APIError ('The parameter to change (' + word + ') does not exist')       


    def __checkInputFilesExist(self):
        """
          :private: This method checks for the existence of a hard coded list of X-Stream input files,
                    i.e. case, grid and executable file.
          
        """
        # First check if all needed files are present
        Casefile='./' + self.config['caseFile']
        Gridfile='./' + self.config['gridFile']
        Executable= self.executable
        
        files_required = [ Casefile, Gridfile, Executable ]
     
        for num, file in enumerate(files_required, 0):    
            case=files_required[num]
            if os.path.exists(case):
                #self.log.info(case + '      ok')
                pass
            else:
                raise APIError.APIError (case + ' does not exist')


    def __setUniformBC(self,property):
        """
          :private: This method is used by setProperty() to set a boundary property in the
                    X-Stream case file.
          
          :param Mupif.Property property: property to change, i.e. temperature or emissivity.
          
        """
        # Open and read the casefile
        Casefile=self.workdir + '/' + self.config['caseFile']
        f_in = open(Casefile,"r")
        lines = f_in.readlines()
        f_in.close()
        
        # defines the lines in which the parameter_to_change for boundary_name_start is found       
        for num, line in enumerate(lines, 1):
           if ( not line.lstrip().startswith('!') ): 
              if re.search( self.config['boundary_name_start'], line, re.IGNORECASE):
                 begin_boundary_line=num
              if re.search( self.config['boundary_name_end'], line, re.IGNORECASE):
                 end_boundary_line=num

        # Which property should be changed and build the new string to be put in the casefile
        # Add 3 spaces at beginning of string to keep layout
        new_value = property.getValue()
        if (property.getPropertyID() == XStPropertyID.PID_Temperature):
           property_to_change = 'TEMPERATURE'
           new_bc_string = '   ' + property_to_change + ' DIRICHLET     UNIFORM ' + str(new_value) + '\n'
        elif (property.getPropertyID() == XStPropertyID.PID_Emissivity):
           property_to_change = 'RADIATION_INTENSITY'
           new_bc_string = '   ' + property_to_change + ' NEUMANN       UNIFORM ' + str(new_value) + '\n'
        else:
           raise APIError.APIError ('Unknown property ID')     
                          
        # Now look for the property_to_change   
        f_out = open(Casefile,"w")
        linenumber = 0
        found_property=False
        for line in lines:
            linenumber = linenumber + 1
            if ( not line.lstrip().startswith('!') ):             

                #introduces the new value of the property only if it is in between lines begin and end
                if ( (re.search( property_to_change, line, re.IGNORECASE)) and (linenumber>begin_boundary_line) and (linenumber<end_boundary_line) ):
                    found_property=True 
                    #self.log.info(('The old boundary condition for ' + property_to_change + ' is: '+ line).strip())
                    self.log.info(('the new boundary condition for ' + property_to_change + ' is: '+ new_bc_string).strip())
                    f_out.write(new_bc_string)

                else:
                    f_out.write(line)  

            # Lines starting with '!' should be simply printed                 
            else:
                f_out.write(line)  
            
        f_out.close()       

        if ( not found_property ):
            raise APIError.APIError('ERROR.' + property_to_change + ' does not exist. Please check the casefile.' + xConf.caseFile)


    def __setDatasetBC(self,field):
        """
          :private: This method is used by setField() to set a 2D boundary condition in
                    the X-Stream case file. The according temporary data files were written
                    by setField(). The temporary data file that matches the 'field' field ID
                    will be inserted to the case file.
          
          :param Mupif.Field field: the 2D boundary condition field
          
        """
        # Open and read the casefile
        Casefile=self.workdir + '/' + self.config['caseFile']
        f_in = open(Casefile,"r")
        lines = f_in.readlines()
        nlines_casefile = len(lines)
        f_in.close()

        # defines the lines in which the field_to_change for the boundary is found       
        for num, line in enumerate(lines, 1):
           if ( not line.lstrip().startswith('!') ): 
              if re.search( self.config['boundary_name_start'], line, re.IGNORECASE):
                 begin_boundary_line=num
              if re.search( self.config['boundary_name_end'], line, re.IGNORECASE):
                 end_boundary_line=num

        # Set the filename of the dataset
        if (field.getFieldID() == XStFieldID.FID_Temperature):
            FieldDatasetName = self.config['Temperature_dataset']
        elif (field.getFieldID() == XStFieldID.FID_Emissivity):            
            FieldDatasetName = self.config['Emissivity_dataset']
        else:
          raise APIError.APIError ('Unknown field ID')

        # Trim the extension of the filename
        DatasetName = os.path.splitext(FieldDatasetName)[0]
        # Which field should be changed and build the new string to be put in the casefile
        # Add 3 spaces at beginning of string to keep layout        
        if (field.getFieldID() == XStFieldID.FID_Temperature):
           field_to_change = 'TEMPERATURE'
           new_bc_string = '   ' + field_to_change + ' DIRICHLET     DATASET ' + DatasetName + '\n'
        elif (field.getFieldID() == XStFieldID.FID_Emissivity):
           field_to_change = 'RADIATION_INTENSITY'
           new_bc_string = '   ' + field_to_change + ' NEUMANN       DATASET ' + DatasetName + '\n'
        else:
           raise APIError.APIError ('Unknown field ID')    
 
        # Check if the file exists and has more than five datapoints
        FieldDatasetName = self.workdir + '/' + FieldDatasetName
        if os.path.exists(FieldDatasetName):
            self.log.info(FieldDatasetName + '      ok')
        else:
            raise APIError.APIError (FieldDatasetName + ' does not exist') 

        npoints_dataset = len(open(FieldDatasetName).readlines())
        if (npoints_dataset<=5):
            self.log.error('Warning. dataset contains 5 or less points. No change in boundary condition will be considered this timestep.')
            return
          
        #store new values            
        DatasetFile=open(FieldDatasetName, 'r+')
        FieldDataset=DatasetFile.readlines()
        DatasetFile.close()

        # First change the boundary condition for the field
        f_out = open(Casefile,"w")
        linenumber = 0
        found_field=False
        for line in lines:
            linenumber = linenumber + 1
            if ( not line.lstrip().startswith('!') ):             

                #introduces the new value of the field only if it is in between lines begin and end
                if ( (re.search( field_to_change, line, re.IGNORECASE)) and (linenumber>begin_boundary_line) and (linenumber<end_boundary_line) ):
                    found_field=True 
                    #self.log.info(('The old boundary condition for ' + field_to_change + ' is: '+ line).strip())
                    self.log.info(('the new boundary condition for ' + field_to_change + ' is: '+ new_bc_string).strip())
                    f_out.write(new_bc_string)

                else:
                    f_out.write(line)  

            # Lines starting with '!' should be simply printed                 
            else:
                f_out.write(line)  
            
        f_out.close()          

        # Now there are 2 options: the dataset is already defined in the case file, than replace the dataset. If not defined, add the 
        # new dataset values

        # Look if the dataset exists and store the lines where it is        
        f_in = open(Casefile,"r")
        lines = f_in.readlines()  
        begin_dataset_line = nlines_casefile
        end_dataset_line = nlines_casefile
        dataset_exists = False
        for num, line in enumerate(lines, 1):
           if ( not line.lstrip().startswith('!') ):                 
           
              if (re.search( 'BEGIN PROFILE', line, re.IGNORECASE) and re.search( DatasetName, line, re.IGNORECASE) and (dataset_exists==False)):
                 begin_dataset_line = num
                 dataset_exists = True

              elif (re.search( 'END PROFILE', line, re.IGNORECASE)) and (begin_dataset_line<num) and (dataset_exists==True):
                 end_dataset_line = num 

        # Rewrite the casefile and replace the dataset values.         
        f_out = open(Casefile,"w")
        linenumber = 0
        for line in lines:
            linenumber = linenumber + 1
            if (linenumber < (begin_dataset_line +2)):
                f_out.write(line)                 
            elif (linenumber==(begin_dataset_line+2)):
                for dataset_line in FieldDataset:
                    if not (dataset_line.lstrip().startswith('!')):
                        f_out.write('   DATA_POINT ' + dataset_line)
            elif (linenumber>=end_dataset_line):
                f_out.write(line)

       # Append the dataset if the dataset is not existing yet
        if ( begin_dataset_line==nlines_casefile ): 
            f_out.write('\n\n')
            f_out.write('BEGIN PROFILE ' + DatasetName + '\n')
            f_out.write('   AXES ' + self.config['boundary_axis1'] + ' ' + self.config['boundary_axis2'] + '\n')
            for dataset_line in FieldDataset:
                if not (dataset_line.lstrip().startswith('!')):
                    f_out.write('   DATA_POINT ' + dataset_line)
            f_out.write('END PROFILE\n')
            
        f_out.close()  
        
        if ( not found_field ):
            raise APIError.APIError('ERROR.' + field_to_change + ' does not exist. Please check the casefile.' + self.config['caseFile'])
          

    def __config(self):
        """
          :private: Read and store the interface and test case specific
                    configuration file which is part of the uploaded input.
          
        """
        if self.config is None:
          # evaluate testcase configuration
          try:
            f = open(self.workdir+'/'+self.file,'r')
          except:
            APIError.APIError ('missing input.in file')
          else:
            s = f.read()
            self.config = ast.literal_eval(s)
            f.close()
            self.__changeValueKeyword('ENSIGHT_PATH',xConf.ensightPath)
        return


                      
         

