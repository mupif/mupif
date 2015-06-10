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
import numpy as np


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

            
class thermal(Application.Application):

    def __init__(self):
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
        self.mesh = Mesh.UnstructuredMesh()
        self.field = None
        # generate a simple mesh here
        self.xl = 0.5 # domain (0..xl)(0..yl)
        self.yl = 0.3
        self.nx = 1 # number of elements in x direction
        self.ny = 1 # number of elements in y direction 
        self.dx = self.xl/self.nx;
        self.dy = self.yl/self.ny;
        self.mesh = meshgen.meshgen((0.,0.), (self.xl, self.yl), self.nx, self.ny) 
    
    def getField(self, fieldID, time):
        if (fieldID == FieldID.FID_Temperature):                
            return self.field
        else:
            raise APIError.APIError ('Unknown field ID')


    def setField(self, field):
        self.Field = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        mesh =  self.mesh
        rule = IntegrationRule.GaussIntegrationRule()
        self.volume = 0.0;
        self.integral = 0.0;

        numNodes = mesh.getNumberOfVertices()
        numElements= mesh.getNumberOfCells()
        ndofs = numNodes

        print numNodes
        print numElements
        print ndofs

        #connectivity 
        c=np.zeros((numElements,4))
        for e in range(0,numElements):
            for i in range(0,4):
                c[e,i]=self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        print "connectivity :",c

        for e in range(0,numElements):
            c0=self.mesh.getVertex(mesh.getCell(e).vertices[0]).coords
            c1=self.mesh.getVertex(mesh.getCell(e).vertices[1]).coords
            c2=self.mesh.getVertex(mesh.getCell(e).vertices[2]).coords
            c3=self.mesh.getVertex(mesh.getCell(e).vertices[3]).coords

        print c0
        print c1
        print c2
        print c3

        length1 = math.fabs(c1[0]-c0[0])
        print length1

        length2 = math.fabs(c2[1]-c1[1])
        print length2

        length3 = math.fabs(c3[0]-c2[0])
        print length3

        length4 = math.fabs(c0[1]-c3[1])
        print length4


        #Global matrix and global vector
        A = np.zeros((4,4 ))
        b = np.zeros((4,1))

        #element matrix and element vector
        A_e = np.zeros((4,4 ))
        b_e = np.zeros((4,1))


        for e in mesh.cells():
            ngp  = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
            pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)
            
            print "e : ",e.number-1
            print "ngp :",ngp
            print "pnts :",pnts

            for p in pnts: # loop over ips
                detJ=e.getTransformationJacobian(p[0])
                print "Jacobian: ",detJ

                dv = detJ * p[1]
                print "dv :",dv 
                
                N = np.zeros((1,4)) 
                tmp = e._evalN(p[0]) 
                N=np.asarray(tmp)
                print "N :",N

                x = e.loc2glob(p[0])
                print "global coords :", x
                
                k=1.
                Grad= np.zeros((2,4))
                Grad = e.compute_B(p[0])
                print "Grad :",Grad
                K=np.zeros((4,4))
                K=k*(np.dot(Grad.T,Grad))

                #Conductivity matrix
                for i in range(4):#loop dofs
                    for j in range(4):
                        A_e[i,j] += K[i,j]*dv   
                print "A_e :",A_e
                print "b_e :",b_e 


                #Add boundary terms
                h=1.
                # boundary_lhs=h*(np.dot(N.T,N))
                boundary_lhs=np.zeros((2,2))
                boundary_lhs[0,0] = (1./3.)*length1*h
                boundary_lhs[0,1] = (1./6.)*length1*h
                boundary_lhs[1,0] = (1./6.)*length1*h
                boundary_lhs[1,1] = (1./3.)*length1*h

                Te = 1.
                # boundary_rhs=h*Te*N.T
                boundary_rhs = np.zeros((2,1)) 
                boundary_rhs[0] = (1./2.)*length1*Te
                boundary_rhs[1] = (1./2.)*length1*Te
        
            # #Assemble
            for i in range(ndofs):#loop nb of dofs
                for j in range(ndofs):
                    A[c[e.number-1,i],c[e.number-1,j]] += A_e[i,j]
                b[c[e.number-1,i]] += b_e[i] 

        #solve linear system
        T = np.linalg.solve(A, b)
        print "T :",T
