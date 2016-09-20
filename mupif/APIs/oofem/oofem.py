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
import sys
sys.path.append('../../..')
from mupif import *
import liboofem

class OOFEM(Application.Application):
    """
    Implementation of OOFEM MuPIF API.
    OOFEM is an object oriented FE solver, see www.oofem.org for details.

    .. automethod:: __init__
    """
    def __init__ (self, file, workdir=''):
        """
        Constructor. Initializes the application.

        :param str file: Name of file
        :param str workdir: Optional parameter for working directory
        """
        super(OOFEM, self).__init__(file, workdir)
        dr = liboofem.OOFEMTXTDataReader(file)
        self.oofem_pb = liboofem.InstanciateProblem(dr,liboofem.problemMode._processor,0)
        self.oofem_pb.checkProblemConsistency()
        self.oofem_mesh = self.oofem_pb.giveDomain(1)
        self.mesh = None # MuPIF representation of oofem mesh

        print "Imported %d node and %d elements"%(self.oofem_mesh.giveNumberOfDofManagers(), self.oofem_mesh.giveNumberOfElements())

    def getField(self, fieldID, time):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        :param FieldID fieldID: Identifier of the field
        :param float time: Target time

        :return: Returns requested field.
        :rtype: Field
        """
        ts=self.oofem_pb.giveCurrentStep()
        self.mesh = self.getMesh(ts)

        print "Mesh conversion finished"
        if (abs(ts.targetTime - time) < 1.e-6):
            values=[]
            ne=self.oofem_mesh.giveNumberOfElements()
            nd=self.oofem_mesh.giveNumberOfDofManagers()
            vmt=liboofem.ValueModeType.VM_Total
            f=self.oofem_pb.giveField(self.getOOFEMFieldName(fieldID), ts)
            print "oofem returned f=",f
            
            for i in range (1, nd+1):
                d=self.oofem_mesh.giveDofManager(i)
                val=f.evaluateAtDman(d,mode=vmt,atTime=ts)
                print "Temp at node ", i, "=", val
                #convert val into tuple
                v = []
                for j in range(len(val)):
                    v.append(val[j])
                values.append(tuple(v))
            return Field.Field(self.mesh, fieldID, ValueType.Scalar, None, time, values)

        else:
            raise APIError.APIError ('Can\'t return field for other than current time step')

    def setField(self, field):
        """
        Registers the given (remote) field in application.

        :param Field field: Remote field to be registered by the application
        """
        raise APIError.APIError ('setField not yet supported')

    def getProperty(self, propID, time, objectID=0):
        """
        Returns property identified by its ID evaluated at given time.

        :param PropertyID propID: property ID
        :param float time: Time when property should to be evaluated
        :param int objectID: Identifies object/submesh on which property is evaluated (optional, default 0)

        :return: Returns representation of requested property
        :rtype: Property
        """
        raise APIError.APIError ('Unknown propertyID')
    def setProperty(self, property, objectID=0):
        """
        Register given property in the application

        :param Property property: Setting property
        :param int objectID: Identifies object/submesh on which property is evaluated (optional, default 0)
        """
        raise APIError.APIError ('Unknown propertyID')
    def getFunction(self, funcID, objectID=0):
        """
        Returns function identified by its ID

        :param FunctionID funcID: function ID
        :param int objectID: Identifies optional object/submesh on which property is evaluated (optional, default 0)

        :return: Returns requested function
        :rtype: Function
        """
        raise APIError.APIError ('Unknown funcID')
    def setFunction(self, func, objectID=0):
        """
        Register given function in the application.

        :param Function func: Function to register
        :param int objectID: Identifies optional object/submesh on which property is evaluated (optional, default 0)
        """
        raise APIError.APIError ('Unknown funcID')


    def getMesh (self, tstep):
        """
        Returns the computational mesh for given solution step.

        :param TimeStep tstep: Solution step
        :return: Returns the representation of mesh
        :rtype: Mesh
        """
        if (self.mesh == None):
            self.mesh = Mesh.UnstructuredMesh()
            vertexlist = []
            celllist   = []
            ne=self.oofem_mesh.giveNumberOfElements()
            nd=self.oofem_mesh.giveNumberOfDofManagers()
            for i in range (1, nd+1):
                d = self.oofem_mesh.giveDofManager(i)
                c = d.giveCoordinates()
                vertexlist.append(Vertex.Vertex(i-1, d.giveLabel(), tuple([c[j] for j in range(len(c))])))
                # print "adding vertex", i
            for i in range (1, ne+1):
                e = self.oofem_mesh.giveElement(i)
                egt = e.giveGeometryType()
                en = e.giveDofManArray()
                # convert en to list
                nodes=tuple([en[n]-1 for n in range(len(en))])
                # print "element ", i, "nodes:", en, nodes
                if (egt == liboofem.Element_Geometry_Type.EGT_triangle_1):
                    celllist.append(Cell.Triangle_2d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                elif (egt == liboofem.Element_Geometry_Type.EGT_quad_1):
                    celllist.append(Cell.Quad_2d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                elif (egt == liboofem.Element_Geometry_Type.EGT_tetra_1):
                    celllist.append(Cell.Tetrahedron_3d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                else:
                    raise APIError.APIError ('Unknown element GeometryType')
                print "adding element ", i
            self.mesh.setup (vertexlist, celllist)
        return self.mesh

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        """
        Solves the problem for given time step.

        Proceeds the solution from actual state to given time.
        The actual state should not be updated at the end, as this method could be
        called multiple times for the same solution step until the global convergence
        is reached. When global convergence is reached, finishStep is called and then
        the actual state has to be updated.
        Solution can be split into individual stages identified by optional stageID parameter.
        In between the stages the additional data exchange can be performed.
        See also wait and isSolved services.

        :param TimeStep tstep: Solution step
        :param int stageID: optional argument identifying solution stage (default 0)
        :param bool runInBackground: optional argument, defualt False. If True, the solution will run in background (in separate thread or remotely).

        """
        ts = self.oofem_pb.generateNextStep()
        print ts
        #override ts settings by the given ones
        ts.setTargetTime(tstep.getTime())
        ts.setIntrinsicTime(tstep.getTime())
        ts.setTimeIncrement(tstep.getTimeIncrement())
        self.oofem_pb.initializeYourself(ts)
        self.oofem_pb.solveYourselfAt(ts)


    def wait(self):
        """
        Wait until solve is completed when executed in background.
        """
    def isSolved(self):
        """
        Check whether solve has completed.

        :return: Returns true or false depending whether solve has completed when executed in background.
        :rtype: bool
        """
    def finishStep(self, tstep):
        """
        Called after a global convergence within a time step is achieved.

        :param TimeStep tstep: Solution step
        """
        self.oofem_pb.updateYourself(self.oofem_pb.giveCurrentStep() )
        self.oofem_pb.terminate(self.oofem_pb.giveCurrentStep())

    def getCriticalTimeStep(self):
        """
        Returns a critical time step for an application.

        :return: Returns the actual (related to current state) critical time step increment
        :rtype: float
        """
    def getAssemblyTime(self, tstep):
        """
        Returns the assembly time related to given time step.
        The registered fields (inputs) should be evaluated in this time.

        :param TimeStep tstep: Solution step
        :return: Assembly time
        :rtype: float, TimeStep
        """
    def storeState(self, tstep):
        """
        Store the solution state of an application.

        :param TimeStep tstep: Solution step
        """
    def restoreState(self, tstep):
        """
        Restore the saved state of an application.
        :param TimeStep tstep: Solution step
        """
    def getAPIVersion(self):
        """
        :return: Returns the supported API version
        :rtype: str, int
        """
        return 1
    def getApplicationSignature(self):
        """
        Get application signature.

        :return: Returns the application identification
        :rtype: str
        """
        return "OOFEM_API"

    def terminate(self):
        """
        Terminates the application. Shutdowns daemons if created internally.
        """
        self.oofem_pb.terminate()
        if self.pyroDaemon:
            self.pyroDaemon.unregister(self)
            if not self.externalDaemon:
                self.pyroDaemon.shutdown()


    def getURI(self):
        """
        :return: Returns the application URI or None if application not registered in Pyro
        :rtype: str
        """
        return self.pyroURI


    def getOOFEMFieldName (self, fieldID):
        if (fieldID == FieldID.FID_Temperature):
            return liboofem.FieldType.FT_Temperature
        else:
            raise APIError.APIError ('Unknown fieldID')            


if __name__ == "__main__":
    o = OOFEM ("test.oofem.in")
    time = 0.0
    dt = 604800.0
    for i in range (10):
        time=i*dt;
        ts = TimeStep.TimeStep(0.0, 604800.0)
        o.solveStep (ts)
        o.finishStep (ts)
        
    f = o.getField(FieldID.FID_Temperature, ts.getTime())
    print "Got field ", f

    #print f.evaluate ((-7.75, -6.1, 0.0))
    f.toVTK2("field1")
