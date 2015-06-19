from mupif import *

import meshgen
import math
import numpy as np
import time as timeTime
import os

import logging
logger = logging.getLogger()#create a logger


def getline (f):
    while True:
        line=f.readline()
        if line == '':
            raise APIError.APIError ('Error: EOF reached in input file')
        elif line[0]!='#':
            return line



class thermal(Application.Application):

    def __init__(self, file, workdir):
        super(thermal, self).__init__(file, workdir)



    def readInput(self):

        dirichletModelEdges=[]
        conventionModelEdges=[]
        try:
            f = open(self.workDir+os.path.sep+self.file, 'r')
            line = getline(f)
            size = line.split()
            self.xl=float(size[0])
            self.yl=float(size[1])

            line = getline(f)
            ne = line.split()
            self.nx=int(ne[0])
            self.ny=int(ne[1])

            for iedge in range(4):
                line = getline(f)
                rec = line.split()
                edge = int(rec[0])
                code = rec[1]
                if (code == 'D'):
                    dirichletModelEdges.append(edge)
                elif (code == 'C'):
                    conventionModelEdges.append(edge)

            f.close()

        except  Exception as e:
            logger.exception(e)
            exit(1)


        self.mesh = Mesh.UnstructuredMesh()
        # generate a simple mesh here
        #self.xl = 0.5 # domain (0..xl)(0..yl)
        #self.yl = 0.3
        #self.nx = 10 # number of elements in x direction
        #self.ny = 10 # number of elements in y direction 
        self.dx = self.xl/self.nx;
        self.dy = self.yl/self.ny;
        self.mesh = meshgen.meshgen((0.,0.), (self.xl, self.yl), self.nx, self.ny) 

        k = 1
        Te=10;

#
# Model edges
#     ----------3----------
#     |                   |
#     4                   2
#     |                   | 
#     ----------1---------
#

        #dirichletModelEdges=(3,4,1)#
        self.dirichletBCs = {}# key is node number, value is prescribed temperature (zero supported only now)
        for ide in dirichletModelEdges:
            #print ide
            if ide == 1:
                for i in range(self.nx+1):
                    self.dirichletBCs[i*(self.ny+1)]=0.0
            elif ide ==2:
                for i in range(self.ny+1):
                    self.dirichletBCs[(self.ny+1)*(self.nx)+i]=0.0
            elif ide ==3:
                for i in range(self.nx+1):
                    self.dirichletBCs[self.ny + (self.ny+1)*(i)]=0.0
            elif ide ==4:
                for i in range(self.ny+1):
                    self.dirichletBCs[i]=0.0

        #conventionModelEdges=(2,)
        self.convectionBC = []
        for ice in conventionModelEdges:
            if ice ==1:
                for i in range(self.nx):
                    self.convectionBC.append((self.ny*i,0,k,Te))
            elif ice ==2:
                for i in range(self.ny):
                    self.convectionBC.append(((self.nx-1)*self.ny+i, 1, k, Te))
            elif ice ==3:
                for i in range(self.nx):
                    self.convectionBC.append((self.ny*(i+1)-1, 2, k, Te))
            elif ice ==4:
                for i in range(self.ny):
                    self.convectionBC.append((i, 3, k, Te))
                

        self.loc=np.zeros(self.mesh.getNumberOfVertices())
        for i in self.dirichletBCs.keys():
            self.loc[i]=-1;
        self.neq = 0;
        for i in range(self.mesh.getNumberOfVertices()):
            if (self.loc[i] >= 0):
                self.loc[i]=self.neq;
                self.neq=self.neq+1

        #print "\tloc:", self.loc
    

    
    def getField(self, fieldID, time):
        if (fieldID == FieldID.FID_Temperature):    

            values=[]
            for i in range (self.mesh.getNumberOfVertices()):
                if (self.dirichletBCs.has_key(i)):
                    values.append((self.dirichletBCs[i],))
                else:
                    values.append((self.T[self.loc[i],0],))
            #print values
            return Field.Field(self.mesh, FieldID.FID_Temperature, ValueType.Scalar, None, 0.0, values);
        else:
            raise APIError.APIError ('Unknown field ID')


    def setField(self, field):
        self.Field = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):

        self.readInput()
        mesh =  self.mesh
        rule = IntegrationRule.GaussIntegrationRule()
        self.volume = 0.0;
        self.integral = 0.0;

        numNodes = mesh.getNumberOfVertices()
        numElements= mesh.getNumberOfCells()
        ndofs = 4

        #print numNodes
        #print numElements
        #print ndofs

        start = timeTime.time()
        print self.getApplicationSignature()
        print "\tNumber of equations:", self.neq

        #connectivity 
        c=np.zeros((numElements,4))
        for e in range(0,numElements):
            for i in range(0,4):
                c[e,i]=self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        #print "connectivity :",c

        #Global matrix and global vector
        A = np.zeros((self.neq, self.neq ))
        b = np.zeros((self.neq, 1))

        print "\tAssembling ..."
        for e in mesh.cells():
            #element matrix and element vector
            A_e = np.zeros((4,4 ))
            b_e = np.zeros((4,1))

            ngp  = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
            pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)

            # print "e : ",e.number-1
            #print "ngp :",ngp
            #print "pnts :",pnts

            for p in pnts: # loop over ips
                detJ=e.getTransformationJacobian(p[0])
                #print "Jacobian: ",detJ

                dv = detJ * p[1]
                #print "dv :",dv 

                N = np.zeros((1,4)) 
                tmp = e._evalN(p[0]) 
                N=np.asarray(tmp)
                #print "N :",N

                x = e.loc2glob(p[0])
                #print "global coords :", x

                k=1.
                Grad= np.zeros((2,4))
                Grad = self.compute_B(e,p[0])
                #print "Grad :",Grad
                K=np.zeros((4,4))
                K=k*(np.dot(Grad.T,Grad))

                #Conductivity matrix
                for i in range(4):#loop dofs
                    for j in range(4):
                        A_e[i,j] += K[i,j]*dv   
            #print "A_e :",A_e
            #print "b_e :",b_e 


            # #Assemble
            #print e, self.loc[c[e.number-1,0]],self.loc[c[e.number-1,1]], self.loc[c[e.number-1,2]], self.loc[c[e.number-1,3]] 
            for i in range(ndofs):#loop nb of dofs
                ii = self.loc[c[e.number-1,i]]
                if (ii>=0):
                    for j in range(ndofs):
                        jj = self.loc[c[e.number-1,j]]
                        if (jj>=0):
                            #print "Assembling", ii, jj
                            A[ii, jj] += A_e[i,j]
                    b[ii] += b_e[i] 

        #print A
        #print b

        # add boundary terms
        for i in self.convectionBC:
            #print "Processing bc:", i
            elem = mesh.getCell(i[0])
            side = i[1]
            h = i[2]
            Te = i[3]

            n1 = elem.getVertices()[side];
            #print n1
            if (side == 3):
                n2 = elem.getVertices()[0]
            else:
                n2 = elem.getVertices()[side+1]

            length = math.sqrt((n2.coords[0]-n1.coords[0])*(n2.coords[0]-n1.coords[0]) +
                               (n2.coords[1]-n1.coords[1])*(n2.coords[1]-n1.coords[1]))

            #print h, Te, length


            # boundary_lhs=h*(np.dot(N.T,N))
            boundary_lhs=np.zeros((2,2))
            boundary_lhs[0,0] = (1./3.)*length*h
            boundary_lhs[0,1] = (1./6.)*length*h
            boundary_lhs[1,0] = (1./6.)*length*h
            boundary_lhs[1,1] = (1./3.)*length*h

            # boundary_rhs=h*Te*N.T
            boundary_rhs = np.zeros((2,1)) 
            boundary_rhs[0] = (1./2.)*length*Te
            boundary_rhs[1] = (1./2.)*length*Te

            # #Assemble
            loci = [n1.number, n2.number]
            #print loci
            for i in range(2):#loop nb of dofs
                ii = self.loc[loci[i]]
                if ii>=0:
                    for j in range(2):
                        jj = self.loc[loci[j]]
                        if jj>=0:
                            #print "Assembling bc ", ii, jj, boundary_lhs[i,j]
                            A[ii,jj] += boundary_lhs[i,j]
                    b[ii] += boundary_rhs[i] 

        #print A
        #print b


        #solve linear system
        print "\tSolving ..."
        self.T = np.linalg.solve(A, b)
        print "\tDone"
        print("\tTime consumed %f s" % (timeTime.time()-start))


    def compute_B(self, elem, lc):
        vertices = elem.getVertices()
        c1=vertices[0].coords
        c2=vertices[1].coords
        c3=vertices[2].coords
        c4=vertices[3].coords

        B11=0.25*(c1[0]-c2[0]-c3[0]+c4[0])
        B12=0.25*(c1[0]+c2[0]-c3[0]-c4[0])
        B21=0.25*(c1[1]-c2[1]-c3[1]+c4[1])
        B22=0.25*(c1[1]+c2[1]-c3[1]-c4[1])

        C11=0.25*(c1[0]-c2[0]+c3[0]-c4[0])
        C12=0.25*(c1[0]-c2[0]+c3[0]-c4[0])
        C21=0.25*(c1[1]-c2[1]+c3[1]-c4[1])
        C22=0.25*(c1[1]-c2[1]+c3[1]-c4[1])

        #local coords
        ksi=lc[0]
        eta=lc[1]

        B = np.zeros((2,2))
        B[0,0] = (1./elem.getTransformationJacobian(lc))*(B22+ksi*C22)  
        B[0,1] = (1./elem.getTransformationJacobian(lc))*(-B21-eta*C21) 
        B[1,0] = (1./elem.getTransformationJacobian(lc))*(-B12-ksi*C12) 
        B[1,1] = (1./elem.getTransformationJacobian(lc))*(B11+eta*C11) 

        dNdksi = np.zeros((2,4))
        dNdksi[0,0] = 0.25 * ( 1. + eta )
        dNdksi[0,1] = -0.25 * ( 1. + eta )
        dNdksi[0,2] = -0.25 * ( 1. - eta )
        dNdksi[0,3] = 0.25 * ( 1. - eta )
        dNdksi[1,0] = 0.25 * ( 1. + ksi )
        dNdksi[1,1] = 0.25 * ( 1. - ksi )
        dNdksi[1,2] = -0.25 * ( 1. - ksi )
        dNdksi[1,3] = -0.25 * ( 1. + ksi )

        Grad= np.zeros((2,4))
        Grad = np.dot(B,dNdksi)

        #print Grad
        return Grad

    def getApplicationSignature(self):
        return "Thermal-demo-solver, ver 1.0"


class mechanical(Application.Application):

    def __init__(self, file, workdir):
        super(mechanical, self).__init__(file, workdir)
        self.E = 1.0;
        self.nu = 0.25;
        self.fx = 0.0
        self.fy = 1.0
        self.temperatureField = None
        self.alpha = 1.0


    def readInput(self):

        dirichletModelEdges=[]
        loadModelEdges=[]
        try:
            f = open(self.workDir+os.path.sep+self.file, 'r')
            line = getline(f)
            size = line.split()
            self.xl=float(size[0])
            self.yl=float(size[1])

            line = getline(f)
            ne = line.split()
            self.nx=int(ne[0])
            self.ny=int(ne[1])

            for iedge in range(4):
                line = getline(f)
                rec = line.split()
                edge = int(rec[0])
                code = rec[1]
                if (code == 'D'):
                    dirichletModelEdges.append(edge)
                elif (code == 'C'):
                    loadModelEdges.append(edge)

            f.close()

        except  Exception as e:
            logger.exception(e)
            exit(1)


        self.mesh = Mesh.UnstructuredMesh()
        # generate a simple mesh here
        #self.xl = 0.5 # domain (0..xl)(0..yl)
        #self.yl = 0.3
        #self.nx = 10 # number of elements in x direction
        #self.ny = 10 # number of elements in y direction 
        self.dx = self.xl/self.nx;
        self.dy = self.yl/self.ny;
        self.mesh = meshgen.meshgen((0.,0.), (self.xl, self.yl), self.nx, self.ny) 

        k = 1
        Te=10;

#
# Model edges
#     ----------3----------
#     |                   |
#     4                   2
#     |                   | 
#     ----------1---------
#

        #dirichletModelEdges=(3,4,1)#
        self.dirichletBCs = {}# key is node number, value is prescribed temperature (zero supported only now)
        for ide in dirichletModelEdges:
            if ide == 1:
                for i in range(self.nx+1):
                    self.dirichletBCs[i*(self.ny+1)]= (0.0, 0.0, 0.0)
            elif ide ==2:
                for i in range(self.ny+1):
                    self.dirichletBCs[self.ny*(self.nx+1)+i]=(0.0,0.0, 0.0)
            elif ide ==3:
                for i in range(self.nx+1):
                    self.dirichletBCs[self.ny+i*(self.nx+1)]=(0.0, 0.0, 0.0)
            elif ide ==4:
                for i in range(self.ny+1):
                    self.dirichletBCs[i]=(0.0, 0.0, 0.0)

        #conventionModelEdges=(2,)
        self.loadBC = []
        fx = self.fx
        fy = self.fy
        for ice in loadModelEdges:
            if ice ==1:
                for i in range(self.nx):
                    self.loadBC.append((self.ny*i,0, fx, fy))
            elif ice ==2:
                for i in range(self.ny):
                    self.loadBC.append(((self.nx-1)*self.ny+i, 1, fx, fy))
            elif ice ==3:
                for i in range(self.nx):
                    self.loadBC.append((self.ny*(i+1)-1, 2, fx, fy))
            elif ice ==4:
                for i in range(self.ny):
                    self.loadBC.append((i, 3, fx, fy))
                

        self.loc=np.zeros((self.mesh.getNumberOfVertices(),2)) # Du, Dv dofs per node
        for i in self.dirichletBCs.keys():
            self.loc[i,0]=-1;
            self.loc[i,1]=-1;
        self.neq = 0;
        for i in range(self.mesh.getNumberOfVertices()):
            for j in range (2): #loop over nodal DOFs
                if (self.loc[i,j] >= 0):
                    self.loc[i,j]=self.neq;
                    self.neq=self.neq+1

        #print "\tloc:", self.loc
    

    
    def getField(self, fieldID, time):
        if (fieldID == FieldID.FID_Displacement):    

            values=[]
            for i in range (self.mesh.getNumberOfVertices()):
                if (self.dirichletBCs.has_key(i)):
                    values.append(self.dirichletBCs[i])
                else:
                    values.append((self.T[self.loc[i,0],0],self.T[self.loc[i,1],0],0.0))
            return Field.Field(self.mesh, FieldID.FID_Temperature, ValueType.Vector, None, 0.0, values);
        else:
            raise APIError.APIError ('Unknown field ID')


    def setField(self, field):
        if (field.getFieldID() == FieldID.FID_Temperature):
            self.temperatureField = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):

        self.readInput()
        mesh =  self.mesh
        rule = IntegrationRule.GaussIntegrationRule()
        self.volume = 0.0;
        self.integral = 0.0;

        numNodes = mesh.getNumberOfVertices()
        numElements= mesh.getNumberOfCells()
        elemNodes = 4
        nodalDofs = 2
        elemDofs = elemNodes*nodalDofs

        #print numNodes
        #print numElements
        #print ndofs

        start = timeTime.time()
        print self.getApplicationSignature()
        print "\tNumber of equations:", self.neq

        #connectivity 
        c=np.zeros((numElements,elemNodes))
        for e in range(0,numElements):
            for i in range(0,elemNodes):
                c[e,i]=self.mesh.getVertex(mesh.getCell(e).vertices[i]).label
        #print "connectivity :",c

        #Global matrix and global vector
        A = np.zeros((self.neq, self.neq ))
        b = np.zeros((self.neq, 1))

        print "\tAssembling ..."
        for e in mesh.cells():
            #element matrix and element vector
            A_e = np.zeros((elemDofs,elemDofs ))
            b_e = np.zeros((elemDofs,1))

            ngp  = rule.getRequiredNumberOfPoints(e.getGeometryType(), 2)
            pnts = rule.getIntegrationPoints(e.getGeometryType(), ngp)

            # print "e : ",e.number-1
            #print "ngp :",ngp
            #print "pnts :",pnts

            for p in pnts: # loop over ips
                detJ=e.getTransformationJacobian(p[0])
                #print "Jacobian: ",detJ

                dv = detJ * p[1]
                #print "dv :",dv 

                N = np.zeros((1,elemNodes)) 
                tmp = e._evalN(p[0]) 
                N=np.asarray(tmp)
                #print "N :",N

                x = e.loc2glob(p[0])
                #print "global coords :", x

                k=1.
                Grad= np.zeros((3,elemDofs))
                Grad = self.compute_B(e,p[0])
                D= self.compute_D(self.E, self.nu)
                #print "Grad :",Grad
                K=np.zeros((elemDofs,elemDofs))
                K=k*(np.dot(Grad.T,np.dot(D, Grad)))

                #Stiffness matrix
                for i in range(elemDofs):#loop dofs
                    for j in range(elemDofs):
                        A_e[i,j] += K[i,j]*dv   

                # temperature load if temperature field registered
                if self.temperatureField:
                    t = self.temperatureField.evaluate(x)
                    et = np.zeros((3,1))
                    et[0]=self.alpha*t[0]
                    et[1]=self.alpha*t[0]
                    et[2]=0.0
                    b_e = np.dot(Grad.T, np.dot(D, et))*dv
            #print "A_e :",A_e
            #print "b_e :",b_e 


            # #Assemble
            #print e, self.loc[c[e.number-1,0]],self.loc[c[e.number-1,1]], self.loc[c[e.number-1,2]], self.loc[c[e.number-1,3]] 
            for i in range(elemNodes):#loop nb of dofs
                for id in range(nodalDofs):
                    ii = self.loc[c[e.number-1,i], id]
                    if (ii>=0):
                        for j in range(elemNodes):
                            for jd in range (nodalDofs):
                                jj = self.loc[c[e.number-1,j], jd]
                                if (jj>=0):
                                    #print "Assembling", ii, jj
                                    A[ii, jj] += A_e[i*nodalDofs+id,j*nodalDofs+jd]
                        b[ii] += b_e[i*nodalDofs+id] 

        #print A
        #print b

        # add boundary terms
        for i in self.loadBC:
            #print "Processing bc:", i
            elem = mesh.getCell(i[0])
            side = i[1]
            fx = i[2] # specified as intensity per edge length
            fy = i[3] # specified as intensity per edge length

            n1 = elem.getVertices()[side];
            #print n1
            if (side == 3):
                n2 = elem.getVertices()[0]
            else:
                n2 = elem.getVertices()[side+1]

            length = math.sqrt((n2.coords[0]-n1.coords[0])*(n2.coords[0]-n1.coords[0]) +
                               (n2.coords[1]-n1.coords[1])*(n2.coords[1]-n1.coords[1]))

            # boundary_rhs=h*Te*N.T
            boundary_rhs = np.zeros((2,2)) 
            boundary_rhs[0,0] = (1./2.)*length*fx
            boundary_rhs[1,0] = (1./2.)*length*fx
            boundary_rhs[0,1] = (1./2.)*length*fy
            boundary_rhs[1,1] = (1./2.)*length*fy

            # #Assemble
            loci = [n1.number, n2.number]
            #print loci
            for i in range(2):#loop nb of nodes
                for id in range(2): #loop over dofs
                    ii = self.loc[loci[i], id]
                    if ii>=0:
                        b[ii] += boundary_rhs[i,id] 

        #print A
        #print b


        #solve linear system
        print "\tSolving ..."
        self.T = np.linalg.solve(A, b)
        print "\tDone"
        print("\tTime consumed %f s" % (timeTime.time()-start))


    def compute_B(self, elem, lc):
        vertices = elem.getVertices()
        c1=vertices[0].coords
        c2=vertices[1].coords
        c3=vertices[2].coords
        c4=vertices[3].coords

        B11=0.25*(c1[0]-c2[0]-c3[0]+c4[0])
        B12=0.25*(c1[0]+c2[0]-c3[0]-c4[0])
        B21=0.25*(c1[1]-c2[1]-c3[1]+c4[1])
        B22=0.25*(c1[1]+c2[1]-c3[1]-c4[1])

        C11=0.25*(c1[0]-c2[0]+c3[0]-c4[0])
        C12=0.25*(c1[0]-c2[0]+c3[0]-c4[0])
        C21=0.25*(c1[1]-c2[1]+c3[1]-c4[1])
        C22=0.25*(c1[1]-c2[1]+c3[1]-c4[1])

        #local coords
        ksi=lc[0]
        eta=lc[1]

        B = np.zeros((2,2))
        B[0,0] = (1./elem.getTransformationJacobian(lc))*(B22+ksi*C22)  
        B[0,1] = (1./elem.getTransformationJacobian(lc))*(-B21-eta*C21) 
        B[1,0] = (1./elem.getTransformationJacobian(lc))*(-B12-ksi*C12) 
        B[1,1] = (1./elem.getTransformationJacobian(lc))*(B11+eta*C11) 

        dNdksi = np.zeros((2,4))
        dNdksi[0,0] = 0.25 * ( 1. + eta )
        dNdksi[0,1] = -0.25 * ( 1. + eta )
        dNdksi[0,2] = -0.25 * ( 1. - eta )
        dNdksi[0,3] = 0.25 * ( 1. - eta )
        dNdksi[1,0] = 0.25 * ( 1. + ksi )
        dNdksi[1,1] = 0.25 * ( 1. - ksi )
        dNdksi[1,2] = -0.25 * ( 1. - ksi )
        dNdksi[1,3] = -0.25 * ( 1. + ksi )

        Grad= np.zeros((2,4))
        Grad = np.dot(B,dNdksi)

        B = np.zeros((3,8))
        B[0,0]=Grad[0,0]
        B[0,2]=Grad[0,1]
        B[0,4]=Grad[0,2]
        B[0,6]=Grad[0,3]

        B[1,1]=Grad[1,0]
        B[1,3]=Grad[1,1]
        B[1,5]=Grad[1,2]
        B[1,7]=Grad[1,3]

        B[2,0]=Grad[1,0]
        B[2,1]=Grad[0,0]
        B[2,2]=Grad[1,1]
        B[2,3]=Grad[0,1]
        B[2,4]=Grad[1,2]
        B[2,5]=Grad[0,2]
        B[2,6]=Grad[1,3]
        B[2,7]=Grad[0,3]
        
        return B

    def compute_D (self, E,nu):
        D = np.zeros((3,3)) 
        ee    = E / ( 1. - nu * nu );
        G = E / ( 2.0 * ( 1. + nu ) );

        D[0,0] = ee;
        D[0,1] = nu * ee;
        D[1,0] = nu * ee;
        D[1,1] = ee;
        D[2,2] = G;
        return D

    def getApplicationSignature(self):
        return "Mechanical-demo-solver, ver 1.0"
