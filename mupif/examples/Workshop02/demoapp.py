from mupif import Application
from mupif import TimeStep
from mupif import APIError
from mupif import PropertyID
from mupif import FieldID
from mupif import Mesh
from mupif import Field
from mupif import ValueType
from mupif import Vertex
from mupif import Cell
from mupif import PyroUtil
from mupif import Property
from mupif import IntegrationRule

import meshgen
import math

class demoapp(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
        self.mesh = Mesh.UnstructuredMesh()
        self.field = None
        # generate a simple mesh here
        self.xl = 10.0 # domain (0..xl)(0..yl)
        self.yl = 10.0
        self.nx = 50 # number of elements in x direction
        self.ny = 50 # number of elements in y direction 
        self.dx = self.xl/self.nx;
        self.dy = self.yl/self.ny;
        self.mesh = meshgen.meshgen((0.,0.), (self.xl, self.yl), self.nx, self.ny) 



    def getField(self, fieldID, time):
        if (fieldID == FieldID.FID_Temperature):
            if (self.field == None):
                #generate sample field
                values=[]
                coeff=8*3.14159265/self.xl
                for ix in range (self.nx+1):
                    for iy in range (self.ny+1):
                        x = ix*self.dx
                        y = iy*self.dy
                        
                        dist = math.sqrt((x-self.xl/2.)*(x-self.xl/2.)+(y-self.yl/2.)*(y-self.yl/2.))
                        val = math.cos(coeff*dist) * math.exp(-4.0*dist/self.xl)
                        values.append((val,))
                self.field=Field.Field(self.mesh, FieldID.FID_Temperature, ValueType.Scalar, None, 0.0, values)
                
            return self.field
        else:
            raise APIError.APIError ('Unknown field ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        return

    def getCriticalTimeStep(self):
        return 1.0

    def getApplicationSignature(self):
        return "Demo app. 1.0"


class minMax(Application.Application):
    """
    Simple application that computes min and max values of the field
    """
    def __init__(self):
        extField = None
    
    def setField(self, field):
        self.extField = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        mesh= self.extField.getMesh()
        self._min = self.extField.evaluate(mesh.getVertex(0).coords)
        self._max = min
        for v in mesh.vertices():
            #print v.coords
            val = self.extField.evaluate(v.coords)
            self._min=min(self._min, val)
            self._max=max(self._max, val)


    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Demo_Min):
            return Property.Property(self._min, PropertyID.PID_Demo_Min, ValueType.Scalar, time, propID, 0)
        elif (propID == PropertyID.PID_Demo_Max):
            return Property.Property(self._max, PropertyID.PID_Demo_Max, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    

class integrateField(Application.Application):
    """
    Simple application that computes integral value of field over 
    its domain and area/volume of the domain
    """
    def __init__(self):
        extField = None
    
    def setField(self, field):
        self.extField = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        mesh = self.extField.getMesh()
        rule = IntegrationRule.GaussIntegrationRule()
        self.volume = 0.0;
        self.integral = 0.0;
        for c in mesh.cells():
            ngp  = rule.getRequiredNumberOfPoints(c.getGeometryType(), 2)
            pnts = rule.getIntegrationPoints(c.getGeometryType(), ngp)
            
            for p in pnts: # loop over ips
                dv=c.getTransformationJacobian(p[0])*p[1]
                self.volume=self.volume+dv
                #print c.loc2glob(p[0])
                self.integral=self.integral+self.extField.evaluate(c.loc2glob(p[0]))[0]*dv

    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Demo_Integral):
            return Property.Property(float(self.integral), PropertyID.PID_Demo_Integral, ValueType.Scalar, time, propID, 0)
        elif (propID == PropertyID.PID_Demo_Volume):
            return Property.Property(float(self.volume), PropertyID.PID_Demo_Volume, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')

            
