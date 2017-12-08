#!/usr/bin/env python

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
#
import sys
import os
sys.path.append('../../..') # Mupif path
sys.path.append('../../APIs/micress') # xstream path
sys.path.append('../../APIs/xstream') # xstream path
from shutil import copyfile
import Pyro4
import time as timeTime
from mupif import *
import logging
log = logging.getLogger()
log.setLevel("INFO")

import mupif.Physics.PhysicalQuantities as PQ
timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])


import clientConfig as cConf

# X-Stream interface
import XStPropertyID
import XStFieldID
import xstream       

# MICRESS interface
import MICPropertyID
import MICFieldID
import micress

#from xstream
import TNO_LU as LU   # local lookup table module (TNO)
import TNO_Qfactor_v1_2 as QFactor # quality factor calculation (TNO)
import Property  # class enhancement for Mupif property class
import util      # Mupif mesh generation utilities
   
  
def runTestCase(xst,mic):
  """
    This method defines the test case procedure itself. It relies on the grid
    setting made in the main method (see parameter). No additional interface objects will be
    allocated here.
    
    First, the initialization of monitor files, lookup table (concentration -> emissivity),
    quality factor module, and a Mupif mesh representing the glass substrates surface is done.
    
    One time step of the overall simulation chain consists of a critical time step of X-Stream
    and a loop over the surface mesh node positions for microstructure analysis by MICRESS
    for the same simulation time. The temperature at each position will be given by 
    X-Stream and serves as a boundary property for MICRESS. After the complete microstructure
    analysis is done, the individual Se concentrations will be mapped by the lookup table to
    emissivity values and assembled to a 2D surface mesh which will serve as a boundary
    condition for the next X-Stream step. Additionally, some properties of the microstructure
    will be combined to a local quality factor, e.g. grain size.
    
    The average of the local quality factors after the last time step is the overall quality
    factor of the photovoltaic thin-film layer. However, there is only data for a few beginning
    time steps given in this example and the quality factor will remain zero.
    
    The main intention of this example is to present one way of implementing a
    simulation chain for Mupif, not to evaluate a CIGS photovoltaic component.
       
    :param Application xst: X-Stream interface handle
    :param tuple mic: A tuple MICRESS Application interface handles
    
  """

  try:
       
    # empty monitor files
    for i in range(len(cConf.monFilenames)):
      f = open(cConf.monFilenames[i],'w')
      f.close()
      
    time  = PQ.PhysicalQuantity(cConf.startTime, 's')

    # initialize TNO converter with lookup table
    lookup = LU.LU(cConf.qfactPrefix + '/' + cConf.qFactInputFiles[0])
    # initialize quality factor calculation
    qfactor = QFactor.QFact(cConf.qfactPrefix + '/' + cConf.qFactInputFiles[1])
    
    # The background mesh for later interpolation determines the macro
    # location for which a microstructure analysis will be done.
    # These locations will be scheduled to the available application interfaces.
    # Schedule scheme: static
    # Chunk size = number of interfaces
    if cConf.debug:
      print ("define background mesh for interpolation",
        cConf.nbX,cConf.nbY, cConf.lenX,cConf.lenY, \
        cConf.originX, cConf.originY, cConf.originZ)
    if ( ( cConf.nbX > 0 ) and ( cConf.nbY > 0 ) ):
      nbX = cConf.nbX
      nbY = cConf.nbY
      lenX = cConf.lenX
      lenY = cConf.lenY
      origin = (cConf.originX, cConf.originY, cConf.originZ)
    elif ( ( cConf.nbX > 0 ) and ( cConf.nbZ > 0 ) ):
      print ("transfer XZ slice to XY coordinates")
      nbX = cConf.nbX
      nbY = cConf.nbZ
      lenX = cConf.lenX
      lenY = cConf.lenZ
      origin = (cConf.originX, cConf.originZ, cConf.originY)
    elif ( ( cConf.nbY > 0 ) and ( cConf.nbZ > 0 ) ):
      print ("transfer YZ slice to XY coordinates")
      nbX = cConf.nbY
      nbY = cConf.nbZ
      lenX = cConf.lenY
      lenY = cConf.lenZ
      origin = (cConf.originY, cConf.originZ, cConf.originX)
    else:
      raise APIError.APIError('no 2D slice recognized') 
    
    bgMesh = util.generateBackgroundMesh(nbX,nbY,lenX,lenY,origin)
    
    # copy nodes for microstructure evaluation to an easy to handle list p
    p = []
    rd = 7
    for node in bgMesh.getVertices():
      if ( ( cConf.nbX > 0 ) and ( cConf.nbY > 0 ) ): # XY
        pNode = ( round(node[0],rd), round(node[1],rd), round(node[2],rd) )
      elif ( ( cConf.nbX > 0 ) and ( cConf.nbZ > 0 ) ): # XZ
        pNode = ( round(node[0],rd), round(node[2],rd), round(node[1],rd) )
      else: # YZ
        pNode = ( round(node[2],rd), round(node[0],rd), round(node[1],rd) )
      p.append(pNode)
    
    timeStepNumber = 0    
    first = True
    profileFirst = True
    eps = 1.0E-8
    timing = []
    files = []
  
    tcStart = timeTime.time() 
    
    # set constant start emissivity (will be modified in homogenization step)
    propEpsXstream = Property.Property( \
                      cConf.startEmissivity, \
                      XStPropertyID.PID_Emissivity, \
                      ValueType.Scalar, time, PQ.getDimensionlessUnit(), 0 )   
    if (cConf.debug):
      print ("set uniform start emissivity: ", propEpsXstream.getValue() )
    xst.setProperty(propEpsXstream)
       
    while ( (time.inUnitsOf(timeUnits).getValue()+eps) < cConf.targetTime ):
    
      print ('Simulation Time: '+ str(time))
      print ('---------------------------')
      # ---------------------------
      # macro step (X-stream)
      # ---------------------------
      # where the critical time step is given by the macro scale output interval,
      # i.e. get the next available output  
      dt = xst.getCriticalTimeStep()#.inUnitsOf(timeUnits).getValue()
      
      time = time + dt
      timeStepNumber = timeStepNumber + 1
      istep = TimeStep.TimeStep(time, dt, cConf.targetTime, timeUnits, timeStepNumber)

      timing.append(timeStepNumber)
      timing.append(time)
      timing.append(dt)
      
      monTempLine = "{0:13s}".format(str(time.getValue()))
    
      # ---------------------------
      # macro step (X-Stream)
      # ---------------------------           
      xst.solveStep(istep,runInBackground=False)       
      
      # get the macro temperature field
      fieldTemperature = xst.getField(FieldID.FID_Temperature, time)
               

      # ---------------------------
      # micro step (MICRESS)
      # for each macro RVE location defined in the vector p
      # ---------------------------
      vT = []
      concSE = []
      avgGrainSize = []
      thicknessCIG = []
      frac4 = [] # Cu(In,GA)3Se5
      frac5 = [] # Cu2-xSe
      frac2 = [] # CIGS
      vQF = [] # local quality factor

      timeMicroStep = 0
      pos = 0         
      while ( pos < len(p) ): # loop over macro locations

        usedInterfaces = len(mic)            
        if ( (pos + usedInterfaces - 1) >= len(p) ):
          # deactivate interfaces which will get no new location, resp. no work to do anymore
          usedInterfaces = len(p) - pos

        for interface in range(usedInterfaces):
    
          # get macro value for temperature, gradient always zero here
          temp = fieldTemperature.evaluate(p[pos+interface])[0]
          tcEnd = timeTime.time()
          timing.append(tcEnd - tcStart)
          
          tcStart = timeTime.time()
          
          # generate Mupif property objects from values
          propLocation = Property.Property( p[pos+interface], MICPropertyID.PID_RVELocation, ValueType.Vector, time, 'm', 0 )
          propT = Property.Property( temp, MICPropertyID.PID_Temperature, ValueType.Scalar, time, 'K', 0 )
          # z-gradient constant at 0.0 at the moment
          propzG = Property.Property( 0.0, MICPropertyID.PID_zTemperatureGradient, ValueType.Scalar, time, 'K/m', 0 )
  
          ## set the properties for micro simulation
          mic[interface].setProperty(propLocation)
          mic[interface].setProperty(propT)
          mic[interface].setProperty(propzG)             
  
          ## make a MICRESS step
          mic[interface].solveStep(istep)

  
        for interface in range(usedInterfaces):

          if cConf.debug:
            print (str(pos+interface)+' ')
            sys.stdout.flush()

          # the call to the solveStep is non-blocking
          # here: wait for finishing time step at each voxel and grab phase fraction results           
          mic[interface].wait()
            
          # grab the results and write them for each voxel in a table
          if ( first ):
            first = False
            # get some general information from the Micress test case,
            # i.e. see variable names
            #pComponentNames = mic[interface].getProperty(MICPropertyID.PID_ComponentNames, time)
            #pPhaseNames = mic[interface].getProperty(MICPropertyID.PID_PhaseNames, time)
            pDimensions = mic[interface].getProperty(MICPropertyID.PID_Dimensions, istep.getTime())
            #componentNames = pComponentNames.getValue()
            #phaseNames = pPhaseNames.getValue()
            dimensions = pDimensions.getValue()
            if cConf.debug:
              print ("Dimensions [um] = ",dimensions[0] * 1E6, dimensions[1] * 1E6, dimensions[2] * 1E6)
          
          pT = mic[interface].getProperty(MICPropertyID.PID_Temperature,istep.getTime())
          pPF = mic[interface].getProperty(MICPropertyID.PID_PhaseFractions,istep.getTime())
          pGS = mic[interface].getProperty(MICPropertyID.PID_AvgGrainSizePerPhase,istep.getTime())
            
          vT.append(pT.getValue())
           
          # calculate se concentration [at%] from phase fractions in thin film (only!)
          #   0 : initial matrix phase, ~ 0 %
          #   2 : Cu (In,Ga) Se2 (CIGS), 1/2 %
          #   4 : Cu (In,Ga)3 Se5, 5/9 %
          #   5 : Cu2-x Se, 1/3 %
          vPF = pPF.getValue() # in %, full fraction means 100 % of complete RVE
          cigsLayerFraction = vPF[0] + vPF[2] + vPF[4] + vPF[5]

          frac4.append(vPF[4]/cigsLayerFraction*100) # Cu(In,GA)3Se5
          frac5.append(vPF[5]/cigsLayerFraction*100) # Cu2-xSe
          frac2.append(vPF[2]/cigsLayerFraction*100) # CIGS

          if (frac4[-1] == 0.0):
            # trick applied because:
            # a zero fraction of Cu(In,GA)3Se5 is the iqf minimum
            # and leads to an overall qf of zero
            # discuss with Jurjen
            frac4[-1] = 1.E-06
            
          c2 = frac2[-1] / 2.
          c4 = frac4[-1] * 5. / 9.
          c5 = frac5[-1] / 3.
          concSE.append((c2+c4+c5))
          if cConf.debug:
            print ("Phase fractions = ", vPF)
            print ("Se concentration = ", concSE[-1])

          # average grain size of grains in the thin film layer
          # the grain size of phase 0 (matrix or liquid) is not defined
          # and not in the vector, i.e. indices have to be shifted left
          vGS = pGS.getValue()
          #avgGS = (vGS[1]+vGS[3]+vGS[4])/3.0  # see comment about indices !!!
          avgGS = vGS[1] # take only CIGS grains
          avgGrainSize.append(avgGS)
          if cConf.debug:
            print ("Average grain size = ", avgGS)
          
          # heuristic for the thickness of the thin film layer
          # homogeneously distributed in xy plane
          # RVE extension in Z [um] * 1E6 * ( CIGS layer phase fractions (0,2,4,5) / 100 )
          CIGSThickness = dimensions[2]* (vPF[0]+vPF[2]+vPF[4]+vPF[5]) * 1E4  # in micrometer
          thicknessCIG.append(CIGSThickness)
          if cConf.debug:
            print ("CIGS thickness [um] = ",CIGSThickness)

          # calculating local quality factors       
          # frac4 = Cu(In,GA)3Se5
          # frac5 = Cu2-xSe
          vQF.append( qfactor.calc ( \
              ( avgGrainSize[-1], thicknessCIG[-1], frac5[-1], frac4[-1] ) ) )
          if cConf.debug:
            print ("Quality factor = ",vQF[-1])

    
        # go to next locations
        pos += usedInterfaces
          
      # ---------------------------
      # end of micro step loop
      # ---------------------------     
              
      tcEnd = timeTime.time()  # take duration from micro step
      timing.append(tcEnd-tcStart)
      if cConf.debug:
        print
      sys.stdout.flush()      

      # ----------------------------------
      # map Se concentration to emissivity
      # ----------------------------------   
      vEm = lookup.convert(concSE)
      if cConf.debug:
        print ("Emissivity values")
        print (vEm)
      
      # --------------------------
      # generate emissivity field
      # --------------------------   
      emissivityValues = []
      for val in vEm:
        emissivityValues.append((val,))
      fieldEmissivity = Field.Field( bgMesh, XStFieldID.FID_Emissivity, \
                          ValueType.Scalar, 'bgMesh', 0.0, emissivityValues )
      #if cConf.debug:
        #print "writing emissivity field"
        #sys.stdout.flush()
      
      #fieldEmissivity.field2VTKData('emissivity').tofile('Em_'+str(timing[-5]).zfill(4))

      # ------------------------------------------------------
      # set emissivity field as an X-Stream boundary condition
      # ------------------------------------------------------   

      # set the emissivity field as a new macro boundary condition
      if cConf.debug:
        print ("setField emissivity for X-Stream")
      tcStart = timeTime.time()   # see end above after xstream.solveStep
      xst.setField(fieldEmissivity)
     
      # write monitor files
      # first column: simulation time
      mon = []
      monLine = "{0:13s}".format(str(time))
      monRange = len(cConf.monFilenames)
      for i in range(monRange): 
        mon.append(monLine)
     
      # write local properties: 
      #  2nd column: average of local values
      #  3rd to nth column: local values
      
      for i in range(len(vT)): # all vectors have the same length
        monLine = "{0:13s}".format(str(round(vT[i],4)))
        mon[0] = mon[0] + monLine 
        if (monRange > 1):
          monLine = "{0:13s}".format(str(round(concSE[i],6)))
          mon[1] = mon[1] + monLine
          monLine = "{0:13s}".format(str(round(avgGrainSize[i],6)))
          mon[2] = mon[2] + monLine
          monLine = "{0:13s}".format(str(round(thicknessCIG[i],6)))
          mon[3] = mon[3] + monLine
          monLine = "{0:13s}".format(str(round(frac5[i],6)))
          mon[4] = mon[4] + monLine
          monLine = "{0:13s}".format(str(round(frac4[i],6)))
          mon[5] = mon[5] + monLine
          monLine = "{0:13s}".format(str(round(vQF[i],6)))
          mon[6] = mon[6] + monLine
          monLine = "{0:13s}".format(str(round(vEm[i],6)))
          mon[7] = mon[7] + monLine
          monLine = "{0:13s}".format(str(round(frac2[i],6)))
          mon[8] = mon[8] + monLine          
      for i in range(monRange):
        f = open(cConf.monFilenames[i],'a')
        f.write(mon[i] + '\n')
        f.close()

      # ---------------------------
      # end of time loop
      # ---------------------------     
           
  except Exception as e:
    log.exception(e)
    raise e
    
  return
        


def main():
    """ 
      The main routine handles all the component's set up.

      This example is fully local, i.e. all application interface objects
      are normal Python objects instantiated by the respective constructors.
      Additionally, appriopriate working directories have to be made.
      The configuration and input files for the participating interfaces
      and external applications have to copied to this working directories.

      After the set up is done, the actual test case will be started with
      the call to 'runTestCase' method.
    """ 
    micressJobs = cConf.micressJobs
    
    start = timeTime.time()
      
    try: # encapsulate all in a try block in order to make sure 
         # that the finally block will be executed
      
      print ("\nSetting up the grid environment")
      print ("  X-Stream interfaces: ",cConf.xstreamJobs)
      print ("  MICRESS interfaces : ",micressJobs)
      
      # -------------------------------------------       
      # allocate macro simulation handle (X-stream)
      # normally one interface
      # -------------------------------------------
      xst = None
      jobsWorkdir = cConf.localWorkdir + "/xstream"
      print ("Creating working directory ... (or reuse existing)")
      print (jobsWorkdir)
      
      # initialize working directory for X-Stream
      # i.e. make directory if necessary,
      #      copy input files 
      if ( not os.path.exists(jobsWorkdir) ):
        #raw_input('Press <ENTER> to confirm. Break with <CTRL-C>.')
        os.mkdir(jobsWorkdir)
      for f in cConf.xstreamInputFiles:
        filename = cConf.xstreamPrefix + '/' + f
        dest = jobsWorkdir + "/" + f
        try:
          copyfile(filename,dest)
        except:
          print ("Error: file copy failed")
          print (filename + ' -> ' + dest)
          
      # get an X-Stream interface object
      try:
        xst = xstream.xstream(workdir=jobsWorkdir, file='input.in')
      except Exception as e:
        log.error('jobsWorkdir %s' % (jobsWorkdir) )
        log.exception(e)


      # -----------------------------------------------------------
      # allocate microstructure interfaces (MICRESS)
      # same procedure as for X-Stream but normally more interfaces
      # -----------------------------------------------------------           
      jobs = 0
      mic = []   
        
      for i in range(micressJobs):
        
        # initialize working directory for MICRESS
        # i.e. make directory if necessary,
        #      copy input files 
        jobsWorkdir = cConf.localWorkdir + "/" + str(jobs)
        print ("Creating working directory ... (or reuse existing)")
        print (jobsWorkdir)
        if ( not os.path.exists(jobsWorkdir) ):
          #raw_input('Press <ENTER> to confirm. Break with <CTRL-C>.')
          os.mkdir(jobsWorkdir)
        for f in cConf.micressInputFiles:
          filename = cConf.micressPrefix + '/' + f            
          dest = jobsWorkdir + "/" + f
          try:
            copyfile(filename,dest)
          except:
            print ("Error: file copy failed")
            print (f + ' -> ' + dest )
            sys.exit()
        
        # get an MICRESS interface object    
        try:
          mic.append(micress.micress(workdir=jobsWorkdir, file='input.in'))
        except Exception as e:
          log.error('jobsWorkdir=%s' % (jobsWorkdir) )
          log.exception(e)
          
        jobs += 1 # count instances


          
      if (xst is not None):
        # print information about grid setting
        print ("\nAllocated interfaces   ")
        print (" " + xst.getApplicationSignature())
        for i in range(jobs):
          print  (" " +str(i) + ": " + mic[i].getApplicationSignature())
        end = timeTime.time()
        print ("\nTime for job allocation: %f s" % (round(end-start,2)))
        print ("---------------------------------------")
        
        # do the actual work !
        start = timeTime.time()
        #raw_input('Press <ENTER> to continue.')
        runTestCase(xst,mic)
        end = timeTime.time()
        
        log.info("\nTime for CIGS example: %f s" % (round(end-start,2)))
        
      else:
        print ("No X-stream interface allocated")
        print ("... skipping MICRESS interface allocation")
    
    except: # logger output for exception will be done before
      pass
    
    
    finally:
            
      start = timeTime.time()
      
      # terminate interfaces
      xst.terminate()
      for i in range(jobs):
        mic[i].terminate()    
      
      end = timeTime.time()
      log.info("\nTime for deallocating jobs: %f s \n" % (round(end-start,2)))


# invoke the main routine
if __name__ == '__main__':
        main()
        log.info("Test OK")
