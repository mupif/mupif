from builtins import range

import sys
import math
sys.path.append('../..')

import mupif
from mupif import *
import mupif.physics.physicalquantities as PQ

timeUnits = PQ.PhysicalUnit('s',   1.,    [0,0,1,0,0,0,0,0,0])
temperatureUnit = PQ.PhysicalUnit('K',   1.,    [0,0,0,0,1,0,0,0,0])


def meshgen_grid2d(origin, size, nx, ny, tria=False, debug=False):
    """ 
    Generates a simple mesh on rectangular domain
    
    :param tuple origin: x,y coordinates of origin (lower left corner) 
    :param tuple size: tuple containing size in x and y directions
    :param int nx: number of elements in x direction
    :param int ny: number of elements in y direction
    :param bool tria: when tru, triangular mesh generated, quad otherwise
    :param bool debug:
    :return: Returns the mesh.
    :rtype: Mesh
    """
    dx = size[0]/nx
    dy = size[1]/ny

    num = 0
    vertexlist = []
    celllist = []

    mesh = mupif.mesh.UnstructuredMesh()
    # generate vertices
    for ix in range(nx+1):
        for iy in range(ny+1):
            if debug:
                print("Adding vertex %d: %f %f %f " % (num, ix*dx, iy*dy, 0.0))
            vertexlist.append(vertex.Vertex(num, num, coords=(origin[0]+1.0*ix*dx, origin[1]+1.0*iy*dy, 0.0)))
            num = num+1

    # generate cells
    num = 1
    for ix in range(nx):
        for iy in range(ny):
            si = iy + ix*(ny+1)  # index of lower left node
            if not tria:
                if debug:
                    print("Adding quad %d: %d %d %d %d" % (num, si, si+ny+1, si+ny+2, si+1))
                celllist.append(cell.Quad_2d_lin(mesh, num, num, vertices=(si, si+ny+1, si+ny+2, si+1)))
                num = num+1
            else:
                if debug:
                    print("Adding tria %d: %d %d %d" % (num, si, si+ny+1, si+ny+2))
                celllist.append(cell.Triangle_2d_lin(mesh, num, num, vertices=(si, si+ny+1, si+ny+2)))
                num = num+1
                if debug:
                    print("Adding tria %d: %d %d %d" % (num, si, si+ny+2, si+1))
                celllist.append(cell.Triangle_2d_lin(mesh, num, num, vertices=(si, si+ny+2, si+1)))
                num = num+1
                
    mesh.setup(vertexlist, celllist)
    return mesh


class AppGridAvg(model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        super(self.__class__,self).__init__(file)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
        self.mesh = mesh.UnstructuredMesh()
        self.field = None
        # generate a simple mesh here
        self.xl = 10.0 # domain (0..xl)(0..yl)
        self.yl = 10.0
        self.nx = 50 # number of elements in x direction
        self.ny = 50 # number of elements in y direction 
        self.dx = self.xl/self.nx;
        self.dy = self.yl/self.ny;
        self.mesh = meshgen_grid2d((0.,0.), (self.xl, self.yl), self.nx, self.ny) 

    def getField(self, fieldID, time):
        if (fieldID == FieldID.FID_Temperature):
            if (self.field == None):
                #generate sample field
                values=[]
                coeff=8*math.pi/self.xl
                for ix in range (self.nx+1):
                    for iy in range (self.ny+1):
                        x = ix*self.dx
                        y = iy*self.dy
                        
                        dist = math.sqrt((x-self.xl/2.)*(x-self.xl/2.)+(y-self.yl/2.)*(y-self.yl/2.))
                        val = math.cos(coeff*dist) * math.exp(-4.0*dist/self.xl)
                        values.append((val,))
                self.field=field.Field(self.mesh, FieldID.FID_Temperature, ValueType.Scalar, temperatureUnit, time, values)
                
            return self.field
        else:
            raise apierror.APIError ('Unknown field ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        return

    def getCriticalTimeStep(self):
        return  PQ.PhysicalQuantity(1.0, 's')

    def getApplicationSignature(self):
        return "Demo app. 1.0"


class AppMinMax(model.Model):
    """
    Simple application that computes min and max values of the field
    """
    def __init__(self):
        super(self.__class__,self).__init__(file)
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
            return property.ConstantProperty(self._min, PropertyID.PID_Demo_Min, ValueType.Scalar, propID, PQ.getDimensionlessUnit(), time=time)
        elif (propID == PropertyID.PID_Demo_Max):
            return property.ConstantProperty(self._max, PropertyID.PID_Demo_Max, ValueType.Scalar, propID, PQ.getDimensionlessUnit(), time=time)
        else:
            raise apierror.APIError ('Unknown property ID')
    

class AppIntegrateField(model.Model):
    """
    Simple application that computes integral value of field over 
    its domain and area/volume of the domain
    """
    def __init__(self):
        super(self.__class__, self).__init__(file)
        self.extField = None

    def setField(self, field):
        self.extField = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        mesh = self.extField.getMesh()
        rule = integrationrule.GaussIntegrationRule()
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
            return property.ConstantProperty(float(self.integral), PropertyID.PID_Demo_Integral, ValueType.Scalar, propID, PQ.getDimensionlessUnit(), time=time)
        elif (propID == PropertyID.PID_Demo_Volume):
            return property.ConstantProperty(float(self.volume), PropertyID.PID_Demo_Volume, ValueType.Scalar, propID, PQ.getDimensionlessUnit(),time=time)
        else:
            raise apierror.APIError ('Unknown property ID')


class AppCurrTime(model.Model):
    """
    Simple application that generates a property (concentration or velocity) with a value equal to actual time
    """
    def __init__(self, file):
        # calls constructor from Application module
        super(self.__class__, self).__init__(file)

    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_Concentration):
            return property.ConstantProperty(self.value, PropertyID.PID_Concentration, ValueType.Scalar, 'kg/m**3', time=time)
        if (propID == PropertyID.PID_Velocity):
            return property.ConstantProperty(self.value, PropertyID.PID_Velocity, ValueType.Scalar, 'm/s', time=time)
        else:
            raise apierror.APIError ('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        time = tstep.getTime().inUnitsOf(timeUnits).getValue()
        self.value=1.0*time

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(0.1, 's')


class AppPropAvg(model.Model):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        super(self.__class__,self).__init__(file)
        self.value = 0.0
        self.count = 0.0
        self.contrib = None

    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return property.ConstantProperty(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 'kg/m**3', time=time)
        else:
            raise apierror.APIError ('Unknown property ID')

    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property
        else:
            raise apierror.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib.getValue(tstep.getTime())
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')

