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
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../../..')
sys.path.append('/home/stanislav/Projects/oofem/build')
sys.path.append('/home/stanislav/Projects/oofem/bindings/python')
import mupif as mp
import oofempy


# shorthands
_EGT = oofempy.Element_Geometry_Type
_FT = oofempy.FieldType
# mapping from oofem element type enumeration to corresponding mupif cell class
elementTypeMap = {
    mp.cellgeometrytype.CGT_TRIANGLE_1:    _EGT.EGT_triangle_1,
    mp.cellgeometrytype.CGT_QUAD:          _EGT.EGT_quad_1,
}
# mapping from mupif field ID to oofem field type
fieldTypeMap = {
    mp.DataID.FID_Displacement:  (_FT.FT_Displacements, 0),
    mp.DataID.FID_Stress: None,
    mp.DataID.FID_Strain: None,
    mp.DataID.FID_Temperature:   (_FT.FT_Temperature, 0),
    mp.DataID.FID_Humidity:      (_FT.FT_HumidityConcentration, 0),
    mp.DataID.FID_Concentration: (_FT.FT_HumidityConcentration, 1),
}


class OOFEM(mp.Model):
    """
    Implementation of OOFEM MuPIF API.
    OOFEM is an object oriented FE solver, see www.oofem.org for details.

    .. automethod:: __init__
    """
    def __init__(self, workDir=''):
        """
        Constructor. Initializes the application.

        :param str workDir: Optional parameter for working directory
        """

        MD = {
            "Name": "OOFEM API",
            "ID": "OOFEM_API",
            "Description": "OOFEM solver",
            "Version_date": "1.0.0, Dec 2022",
            # "Geometry": "2D rectangle",
            # "Boundary_conditions": "Dirichlet, Neumann",
            "Inputs": [
                {
                    "Name": "Input file",
                    "Type": "mupif.PyroFile",
                    "Required": True,
                    "Type_ID": "mupif.DataID.ID_InputFile",
                    "Obj_ID": "input_file",
                    "Set_at": "initialization",
                    "Units": "none"
                }
            ],
            "Outputs": [
                # {
                #     "Name": "temperature",
                #     "Type_ID": "mupif.DataID.FID_Temperature",
                #     "Type": "mupif.Field",
                #     "Required": False,
                #     "Units": "degC"
                # }
            ],
            "Solver": {
                "Software": "OOFEM",
                "Type": "Finite elements",
                "Accuracy": "High",
                "Sensitivity": "Low",
                "Complexity": "High",
                "Robustness": "High",
                "Estim_time_step_s": 1,
                "Estim_comp_time_s": 1,
                "Estim_execution_cost_EUR": 0.01,
                "Estim_personnel_cost_EUR": 0.01,
                "Required_expertise": "None",
                "Language": "C++",
                "License": "LGPL",
                "Creator": "Borek Patzak",
                "Version_date": "1.0.0, Dec 2022",
                "Documentation": "oofem.org"
            },
            "Physics": {
                "Type": "Continuum",
                "Entity": "Finite elements",
                "Equation": [],
                "Equation_quantities": [],
                "Relation_description": [],
                "Relation_formulation": [],
                "Representation": "Finite elements"
            }
        }

        super().__init__(workDir=workDir, metadata=MD)

        dr = oofempy.OOFEMTXTDataReader("testt.oofem.in")
        # dr = oofempy.DataReader("testt.oofem.in")
        # dr = oofempy.OOFEMTXTDataReader(file)
        self.oofem_pb = oofempy.InstanciateProblem(dr, oofempy.problemMode.processor, 0, None, False)
        self.oofem_pb.checkProblemConsistency()
        self.oofem_mesh = self.oofem_pb.giveDomain(1)
        self.mesh = None  # MuPIF representation of oofem mesh

        print("Imported %d node and %d elements" % (self.oofem_mesh.giveNumberOfDofManagers(), self.oofem_mesh.giveNumberOfElements()))

    def getField(self, fieldID, time):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        :param mp.DataID fieldID: Identifier of the field
        :param  time: Target time

        :return: Returns requested field.
        :rtype: Field
        """
        ts = self.oofem_pb.giveCurrentStep()
        self.mesh = self.getMesh(ts)

        # print "Mesh conversion finished"
        if abs(ts.targetTime - time.inUnitsOf('s').getValue()) < 1.e-6:
            values = []
            ne = self.oofem_mesh.giveNumberOfElements()
            nd = self.oofem_mesh.giveNumberOfDofManagers()
            vmt = oofempy.ValueModeType.VM_Total
            f = self.oofem_pb.giveField(self.getOOFEMFieldName(fieldID), ts)
            # print "oofem returned f=",f
            if not f:
                raise ValueError("no suitable field in solver found")
            
            for i in range(1, nd+1):
                d = self.oofem_mesh.giveDofManager(i)
                val = f.evaluateAtDman(d, mode=vmt, atTime=ts)
                # print "Temp at node ", i, "=", val
                # convert val into tuple
                v = []
                for j in range(len(val)):
                    v.append(val[j])
                values.append(tuple(v))
            return mp.Field(self.mesh, fieldID, mp.ValueType.Scalar, None, time, values)

        else:
            raise mp.APIError('Can\'t return field for other than current time step')

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.Field):
            """
            Registers the given (remote) object or parameter in application.
    
            :param Field obj: Remote object or parameter to be registered by the application
            """
            # convert field.Field into oofempy.UnstructredGridField first
            mesh = obj.getMesh()
            target = oofempy.UnstructuredGridField(mesh.getNumberOfVertices(), mesh.getNumberOfCells())
            # convert vertices first
            for node in mesh.vertices():
                c = node.getCoordinates()  # tuple -> FloatArray conversion
                cc = oofempy.FloatArray(len(c))
                for i in range(len(c)):
                    cc[i] = c[i]
                target.addVertex(node.getNumber(), cc)
            for cell in mesh.cells():
                v = cell.getVertices()
                vv = oofempy.IntArray(len(v))
                for i in range(len(v)):
                    vv[i]=v[i].getNumber()
                target.addCell(cell.number, elementTypeMap.get(cell.getGeometryType()), vv)
            # set values
            if obj.getFieldType() == mp.FieldType.FT_vertexBased:
                for node in mesh.vertices():
                    target.setVertexValue(node.getNumber(), obj.getVertexValue(node.getNumber()))
            else:
                for node in mesh.vertices():
                    target.setVertexValue(node.getNumber(), obj.evaluate(node.getCoordinates()))
            # register converted field in oofem
            ft = fieldTypeMap.get((obj.getFieldID()))[0]
            if ft is None:
                raise ValueError("Field type not recognized")
            print("oofem: registering extermal field ", obj, "as ...", target)
            # print "Check: ", field.evaluate((2.5,0.9,0)), " == ", target.evaluateAtPos (t2f((2.5,0.9,0)), oofempy.ValueModeType.VM_Total)

            self.oofem_pb.giveContext().giveFieldManager().registerField(target, ft)
            # internal check
            # checkf = self.oofem_pb.giveContext().giveFieldManager().giveField(oofempy.FieldType.FT_Temperature)
            # print checkf
            # print "Controll evaluation = ", checkf.evaluateAtPos (t2f((2.5,0.9,0)), oofempy.ValueModeType.VM_Total)

    def getProperty(self, propID, time, objectID=""):
        """
        Returns property identified by its ID evaluated at given time.

        :param DataID propID: property ID
        :param float time: Time when property should to be evaluated
        :param int objectID: Identifies object/submesh on which property is evaluated (optional, default 0)

        :return: Returns representation of requested property
        :rtype: Property
        """
        raise mp.APIError('Unknown propertyID')

    def getFunction(self, funcID, objectID=""):
        """
        Returns function identified by its ID

        :param DataID funcID: function ID
        :param int objectID: Identifies optional object/submesh on which property is evaluated (optional, default 0)

        :return: Returns requested function
        :rtype: Function
        """
        raise mp.APIError('Unknown funcID')

    def getMesh(self, tstep):
        """
        Returns the computational mesh for given solution step.

        :param TimeStep tstep: Solution step
        :return: Returns the representation of mesh
        :rtype: Mesh
        """
        if self.mesh is None:
            self.mesh = mp.UnstructuredMesh()
            vertexlist = []
            celllist = []
            ne = self.oofem_mesh.giveNumberOfElements()
            nd = self.oofem_mesh.giveNumberOfDofManagers()
            for i in range(1, nd+1):
                d = self.oofem_mesh.giveDofManager(i)
                c = d.giveCoordinates()
                vertexlist.append(mp.Vertex(i-1, d.giveLabel(), tuple([c[j] for j in range(len(c))])))
                # print "adding vertex", i
            for i in range(1, ne+1):
                e = self.oofem_mesh.giveElement(i)
                egt = e.giveGeometryType()
                en = e.giveDofManArray()
                # convert en to list
                nodes = tuple([en[n]-1 for n in range(len(en))])
                # print "element ", i, "nodes:", en, nodes
                if egt == oofempy.Element_Geometry_Type.EGT_triangle_1:
                    celllist.append(mp.Triangle_2d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                elif egt == oofempy.Element_Geometry_Type.EGT_quad_1:
                    celllist.append(mp.Quad_2d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                elif egt == oofempy.Element_Geometry_Type.EGT_tetra_1:
                    celllist.append(mp.Tetrahedron_3d_lin(self.mesh, i-1, e.giveLabel(), nodes))
                else:
                    raise mp.APIError('Unknown element GeometryType')
                # print "adding element ", i
            self.mesh.setup(vertexlist, celllist)
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
        self.oofem_pb.preInitializeNextStep()
        self.oofem_pb.giveNextStep()
        currentStep = self.oofem_pb.giveCurrentStep()
        self.oofem_pb.initializeYourself(currentStep)
        self.oofem_pb.solveYourselfAt(currentStep)
        self.oofem_pb.updateYourself(currentStep)
        self.oofem_pb.terminate(currentStep)
        print("TimeStep %d finished" % tstep.getNumber())

        # ts = self.oofem_pb.giveNextStep()
        # print ts
        # override ts settings by the given ones
        # ts.setTargetTime(tstep.getTime().getValue())
        # ts.setIntrinsicTime(tstep.getTime().getValue())
        # ts.setTimeIncrement(tstep.getTimeIncrement().getValue())
        # self.oofem_pb.initializeYourself(ts)
        # self.oofem_pb.solveYourselfAt(ts)

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
        self.oofem_pb.updateYourself(self.oofem_pb.giveCurrentStep())
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

    def getOOFEMFieldName(self, fieldID):
        if fieldID == mp.DataID.FID_Temperature:
            return oofempy.FieldType.FT_Temperature
        else:
            raise mp.APIError('Unknown fieldID')


if __name__ == "__main__":

    # def t2f(t):
    #     # conver tuple to floatArray
    #     ans = oofempy.FloatArray(len(t))
    #     for i in range(len(t)):
    #         ans[i] = t[i]
    #     return ans
    #
    # def t2i(t):
    #     # conver tuple to floatArray
    #     ans = oofempy.IntArray(len(t))
    #     for i in range(len(t)):
    #         ans[i] = t[i]
    #     return ans
    #
    #
    # f = oofempy.UnstructuredGridField(9, 4)
    # f.addVertex(0, t2f((0,0,0)))
    # f.addVertex(1, t2f((1,0,0)))
    # f.addVertex(2, t2f((2,0,0)))
    #
    # f.addVertex(3, t2f((0,0.5,0)))
    # f.addVertex(4, t2f((1,0.5,0)))
    # f.addVertex(5, t2f((2,0.5,0)))
    #
    # f.addVertex(6, t2f((0,1,0)))
    # f.addVertex(7, t2f((1,1,0)))
    # f.addVertex(8, t2f((2,1,0)))
    #
    # f.addCell(0, _EGT.EGT_quad_1, t2i((0,1,4,3)))
    # f.addCell(1, _EGT.EGT_quad_1, t2i((1,2,5,4)))
    # f.addCell(2, _EGT.EGT_quad_1, t2i((3,4,7,6)))
    # f.addCell(3, _EGT.EGT_quad_1, t2i((4,5,8,7)))
    #
    #
    # for i in range(9):
    #     f.setVertexValue(i,t2f((i%3,)))
    #     print (i, i%3)
    #
    # print (f.evaluateAtPos (t2f((2,1,0)), oofempy.ValueModeType.VM_Total))

    if 1:
        ot = OOFEM()  # "testt.oofem.in"
        # om = OOFEM("testm.oofem.in")
        time = 0.0
        dt = 0.1
        targetTime = 1.
        for i in range(10):
            time = i*dt
            ts = mp.TimeStep(time=time, dt=dt, targetTime=targetTime, unit=mp.U.s, number=i)
            ot.solveStep(ts)
            ot.finishStep(ts)
            
            f = ot.getField(mp.DataID.FID_Temperature, ts.getTime().getValue())
            f.toVTK2("temp%d" % i)
            # print f.evaluate ((2.5, 0.9, 0.0))
            # print "Got field ", f
            # om.set(f)
            # om.solveStep(ts)
            # om.finishStep(ts)

    #

    # o = OOFEM ("test.oofem.in")
    # time = 0.0
    # dt = 604800.0

    # for i in range (2):
    #     time=i*dt;
    #     ts = timestep.TimeStep(time, 604800.0)
    #     o.solveStep (ts)
    #     o.finishStep (ts)
        
    # f = o.getField(DataID.FID_Temperature, ts.getTime())
    # print "Got field ", f

    # #print f.evaluate ((-7.75, -6.1, 0.0))
    # f.toVTK2("field1")

    # o2 = OOFEM ("test.oofem.in")
    # o2.set(f)
