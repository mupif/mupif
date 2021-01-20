# Static analysis for cantilever beam loaded by a uniform vertical distributed load.
# A user enters geometry, meshing details, material properties and distributed load.
# App1 uses 2D plane stress model.
# App2 uses simple Euler-Bernoulli beam model neglecting shear deformation.
# Created 03/2018

import sys
sys.path.append('../../..')
import demoapp
from mupif import *
import logging
log = logging.getLogger()

# Compulsory parameters for the simulation
thickness = 0.01     # Beam (plane) thickness (m)
height = 1.0         # Beam height (m)
length = 5.0         # Beam length (m)
Emodulus = 30.0e+9   # E modulus (Pa)
PoissonRatio = 0.25  # Poisson's ratio (-)
distribLoad = 2e+2   # Distributed vertical load (N/m)

# Optional parameters for meshing
numX = 20  # Number of finite elements in X direction
numY = 8  # Number of finite elements in Y direction
fileName = 'cantilever1.in'


def createAppInputFile():
    inFile = open(fileName, 'w')
    inFile.write('%f %f\n' % (length, height))
    inFile.write('%d %d\n' % (numX, numY))
    inFile.write('%f\n' % thickness)
    inFile.write('%e %f\n' % (Emodulus, PoissonRatio))
    inFile.write('0.0\n')
    inFile.write('1 N\n2 N\n3 C 0. %f\n4 D\n' % -distribLoad)
    inFile.close()


# Input data for app1 are in cantilever1.in
createAppInputFile()
tstep = timestep.TimeStep(1., 1., 10, 's')
app1 = demoapp.mechanical(fileName, '.')
sol = app1.solveStep(tstep) 
f = app1.getField(FieldID.FID_Displacement, tstep.getTargetTime())
f.field2VTKData().tofile('cantilever1.vtk')
# f.field2Image2D(fieldComponent=1, title='Displacement', fileName='cantilever1.png')
# right bottom point
# time.sleep(2)
maxDeflection = -f.evaluate((app1.xl, 0., 0)).getValue()[1]
log.info("Max. deflection from plane-stress task (m): %.3e" % maxDeflection)

app2 = demoapp.EulerBernoulli(b=thickness, h=height, L=length, E=Emodulus, f=distribLoad)
app2.solveStep(tstep)
maxDeflection = app2.getField(FieldID.FID_Displacement, tstep.getTargetTime())
log.info("Max. deflection from Euler-Bernoulli beam (m): %.3e" % maxDeflection)
