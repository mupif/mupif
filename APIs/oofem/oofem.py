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
import Pyro5
import tempfile
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


@Pyro5.api.expose
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
                {
                    "Name": "temperature",
                    "Type_ID": "mupif.DataID.FID_Temperature",
                    "Type": "mupif.Field",
                    "Units": "degC"
                }
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
                "Entity": "Other",
                "Equation": [],
                "Equation_quantities": [],
                "Relation_description": [],
                "Relation_formulation": [],
                "Representation": "Finite elements"
            }
        }

        super().__init__(workDir=workDir, metadata=MD)

        self.oofem_pb = None
        self.oofem_mesh = None
        self.mesh = None  # MuPIF representation of oofem mesh

    def initialize(self, workdir='', metadata=None, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def set(self, obj, objectID=""):
        if obj.isInstance(mp.PyroFile):
            if obj.getDataID() == mp.DataID.ID_InputFile:
                with tempfile.TemporaryDirectory(dir="/tmp", prefix='OOFEM') as tempDir:
                    filename = tempDir + os.path.sep + 'local_input_file.in'
                    mp.PyroFile.copy(obj, filename)
                    dr = oofempy.OOFEMTXTDataReader(filename)
                    self.oofem_pb = oofempy.InstanciateProblem(dr, oofempy.problemMode.processor, 0, None, False)
                    self.oofem_pb.checkProblemConsistency()
                    self.oofem_mesh = self.oofem_pb.giveDomain(1)
                    self.oofem_pb.init()
                    self.oofem_pb.postInitialize()
                    activeMStep = self.oofem_pb.giveMetaStep(1)
                    self.oofem_pb.initMetaStepAttributes(activeMStep)

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
                    vv[i] = v[i].getNumber()
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

    def get(self, objectTypeID, time=None, objectID=""):
        """
        Returns the requested field at given time. Field is identified by fieldID.

        :param mp.DataID objectTypeID: Identifier of the field
        :param  time: Target time
        :param  objectID:

        :return: Returns requested field.
        :rtype: Field
        """
        current_step = self.oofem_pb.giveCurrentStep()
        self.mesh = self.getMesh()

        if abs(current_step.giveTargetTime() - time.inUnitsOf('s').getValue()) < 1.e-6:
            values = []
            ne = self.oofem_mesh.giveNumberOfElements()
            nd = self.oofem_mesh.giveNumberOfDofManagers()
            vmt = oofempy.ValueModeType.VM_Total
            f = self.oofem_pb.giveField(self.getOOFEMFieldName(objectTypeID), current_step)
            if not f:
                raise ValueError("no suitable field in solver found")

            for i in range(1, nd+1):
                d = self.oofem_mesh.giveDofManager(i)
                val = f.evaluateAt(d.giveCoordinates(), vmt, current_step)
                v = []
                for j in range(len(val)):
                    v.append(val[j])
                values.append(tuple(v))
            return mp.Field(self.mesh, objectTypeID, mp.ValueType.Scalar, None, time, values)

        else:
            raise mp.APIError('Can\'t return field for other than current time step')

    def getMesh(self):
        """
        Returns the computational mesh for given solution step.

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
                vertexlist.append(mp.Vertex(number=i-1, label=i-1, coords=tuple([coord for coord in c])))
                # print "adding vertex", i
            for i in range(1, ne+1):
                e = self.oofem_mesh.giveElement(i)
                egt = e.giveGeometryType()
                en = e.giveDofManArray()
                # convert en to list
                nodes = tuple([eni-1 for eni in en])
                # print "element ", i, "nodes:", en, nodes
                if egt == oofempy.Element_Geometry_Type.EGT_triangle_1:
                    celllist.append(mp.Triangle_2d_lin(mesh=self.mesh, number=i-1, label=i-1, vertices=nodes))
                elif egt == oofempy.Element_Geometry_Type.EGT_quad_1:
                    celllist.append(mp.Quad_2d_lin(mesh=self.mesh, number=i-1, label=i-1, vertices=nodes))
                elif egt == oofempy.Element_Geometry_Type.EGT_tetra_1:
                    celllist.append(mp.Tetrahedron_3d_lin(mesh=self.mesh, number=i-1, label=i-1, vertices=nodes))
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
        print("TimeStep %d finished" % tstep.getNumber())

    def finishStep(self, tstep):
        """
        Called after a global convergence within a time step is achieved.

        :param TimeStep tstep: Solution step
        """
        self.oofem_pb.updateYourself(self.oofem_pb.giveCurrentStep())
        self.oofem_pb.terminate(self.oofem_pb.giveCurrentStep())

    def getCriticalTimeStep(self):
        return 1000.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

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


if __name__ == '__main__':
    import oofem
    ns = mp.pyroutil.connectNameserver()
    mp.SimpleJobManager(
        ns=ns,
        appClass=oofem.OOFEM,
        appName='OOFEM_API',
        maxJobs=10
    ).runServer()
